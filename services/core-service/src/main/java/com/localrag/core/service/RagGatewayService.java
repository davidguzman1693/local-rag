package com.localrag.core.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.localrag.core.client.AiEngineClient;
import com.localrag.core.model.ChatSession;
import com.localrag.core.model.ChunkRecord;
import com.localrag.core.model.Citation;
import com.localrag.core.model.DocumentSummary;
import com.localrag.core.model.IngestResponse;
import com.localrag.core.model.QueryRequest;
import com.localrag.core.model.QueryResponse;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import reactor.core.publisher.Flux;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicReference;

@Service
public class RagGatewayService {

    private final AiEngineClient aiEngineClient;
    private final ChatSessionService chatSessionService;
    private final ObjectMapper objectMapper;

    private record LocalDocMetadata(Long fileSizeBytes, Instant uploadedAt) {}

    private final Map<String, LocalDocMetadata> documentMetadataStore = new ConcurrentHashMap<>();

    public RagGatewayService(
            AiEngineClient aiEngineClient,
            ChatSessionService chatSessionService,
            ObjectMapper objectMapper
    ) {
        this.aiEngineClient = aiEngineClient;
        this.chatSessionService = chatSessionService;
        this.objectMapper = objectMapper;
    }

    public Map<String, Object> checkSystemHealth() {
        Map<String, Object> aiHealth = aiEngineClient.checkHealth();
        boolean aiHealthy = "healthy".equals(aiHealth.get("status"));
        return Map.of(
                "status", aiHealthy ? "healthy" : "degraded",
                "gateway", "core-service",
                "ai_engine", aiHealth,
                "active_sessions", chatSessionService.listSessions().size()
        );
    }

    public IngestResponse uploadDocument(MultipartFile file) {
        long size = file.getSize();
        IngestResponse response = aiEngineClient.uploadDocument(file);
        if (response != null && response.documentId() != null) {
            documentMetadataStore.put(response.documentId(), new LocalDocMetadata(size, Instant.now()));
        }
        return response;
    }

    public List<DocumentSummary> listDocuments() {
        List<DocumentSummary> rawDocs = aiEngineClient.listDocuments();
        if (rawDocs == null) {
            return List.of();
        }
        return rawDocs.stream()
                .map(doc -> {
                    LocalDocMetadata meta = documentMetadataStore.get(doc.documentId());
                    return new DocumentSummary(
                            doc.documentId(),
                            doc.sourceFilename(),
                            doc.chunkCount(),
                            meta != null ? meta.fileSizeBytes() : doc.fileSizeBytes(),
                            meta != null ? meta.uploadedAt() : doc.uploadedAt()
                    );
                })
                .toList();
    }

    public List<ChunkRecord> getDocumentChunks(String documentId) {
        return aiEngineClient.getDocumentChunks(documentId);
    }

    public Map<String, Object> deleteDocument(String documentId) {
        documentMetadataStore.remove(documentId);
        return aiEngineClient.deleteDocument(documentId);
    }

    public QueryResponse query(QueryRequest request) {
        ChatSession session = chatSessionService.getOrCreateSession(request.sessionId(), request.query());
        QueryResponse aiResponse = aiEngineClient.query(request);
        chatSessionService.appendExchange(
                session.id(),
                request.query(),
                aiResponse.answer(),
                aiResponse.citations()
        );
        return aiResponse.withSessionId(session.id());
    }

    public Flux<ServerSentEvent<String>> streamQuery(QueryRequest request) {
        ChatSession session = chatSessionService.getOrCreateSession(request.sessionId(), request.query());
        StringBuilder answerBuffer = new StringBuilder();
        AtomicReference<List<Citation>> capturedCitations = new AtomicReference<>(new ArrayList<>());

        ServerSentEvent<String> sessionEvent = ServerSentEvent.<String>builder()
                .data("{\"type\":\"session\",\"session_id\":\"" + session.id() + "\"}")
                .build();

        Flux<ServerSentEvent<String>> aiEventStream = aiEngineClient.streamQuery(request)
                .filter(chunk -> chunk != null && !chunk.isBlank())
                .doOnNext(chunk -> {
                    try {
                        JsonNode node = objectMapper.readTree(chunk);
                        String type = node.path("type").asText("");
                        if ("token".equals(type)) {
                            answerBuffer.append(node.path("token").asText(""));
                        } else if ("citations".equals(type) && node.has("citations")) {
                            List<Citation> parsed = objectMapper.convertValue(
                                    node.get("citations"),
                                    new TypeReference<List<Citation>>() {}
                            );
                            capturedCitations.set(parsed);
                        }
                    } catch (Exception ignored) {
                        // Forward raw SSE chunk even if JSON inspection fails
                    }
                })
                .map(chunk -> ServerSentEvent.<String>builder().data(chunk).build())
                .doOnComplete(() -> {
                    if (!answerBuffer.isEmpty()) {
                        chatSessionService.appendExchange(
                                session.id(),
                                request.query(),
                                answerBuffer.toString(),
                                capturedCitations.get()
                        );
                    }
                });

        return Flux.concat(Flux.just(sessionEvent), aiEventStream);
    }
}

