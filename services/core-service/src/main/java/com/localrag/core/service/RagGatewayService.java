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
import com.localrag.core.model.SearchDebugResponse;
import com.localrag.core.persistence.DocumentMetadataEntity;
import com.localrag.core.persistence.DocumentMetadataRepository;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import reactor.core.publisher.Flux;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
public class RagGatewayService {

    private final AiEngineClient aiEngineClient;
    private final ChatSessionService chatSessionService;
    private final DocumentMetadataRepository documentMetadataRepository;
    private final ObjectMapper objectMapper;

    public RagGatewayService(
            AiEngineClient aiEngineClient,
            ChatSessionService chatSessionService,
            DocumentMetadataRepository documentMetadataRepository,
            ObjectMapper objectMapper
    ) {
        this.aiEngineClient = aiEngineClient;
        this.chatSessionService = chatSessionService;
        this.documentMetadataRepository = documentMetadataRepository;
        this.objectMapper = objectMapper;
    }

    public Map<String, Object> checkSystemHealth() {
        Map<String, Object> aiHealth = aiEngineClient.checkHealth();
        boolean aiHealthy = "healthy".equals(aiHealth.get("status"));
        return Map.of(
                "status", aiHealthy ? "healthy" : "degraded",
                "gateway", "core-service",
                "persistence", "h2-jpa",
                "ai_engine", aiHealth,
                "active_sessions", chatSessionService.listSessions().size()
        );
    }

    public IngestResponse uploadDocument(MultipartFile file) {
        Long size = file.getSize();
        IngestResponse response = aiEngineClient.uploadDocument(file);
        if (response != null && response.documentId() != null) {
            documentMetadataRepository.save(new DocumentMetadataEntity(
                    response.documentId(),
                    response.filename() != null ? response.filename() : "unknown",
                    size,
                    Instant.now()
            ));
        }
        return response;
    }

    public List<DocumentSummary> listDocuments() {
        List<DocumentSummary> rawDocs = aiEngineClient.listDocuments();
        if (rawDocs == null || rawDocs.isEmpty()) {
            return List.of();
        }

        Map<String, DocumentMetadataEntity> metadataMap = documentMetadataRepository.findAll().stream()
                .collect(Collectors.toMap(DocumentMetadataEntity::getDocumentId, Function.identity()));

        return rawDocs.stream()
                .map(doc -> {
                    DocumentMetadataEntity meta = doc.documentId() != null
                            ? metadataMap.get(doc.documentId())
                            : null;
                    return new DocumentSummary(
                            doc.documentId(),
                            doc.sourceFilename(),
                            doc.chunkCount(),
                            meta != null ? meta.getFileSizeBytes() : doc.fileSizeBytes(),
                            meta != null ? meta.getUploadedAt() : doc.uploadedAt()
                    );
                })
                .toList();
    }

    public List<ChunkRecord> getDocumentChunks(String documentId) {
        return aiEngineClient.getDocumentChunks(documentId);
    }

    public Map<String, Object> deleteDocument(String documentId) {
        if (documentId != null && documentMetadataRepository.existsById(documentId)) {
            documentMetadataRepository.deleteById(documentId);
        }
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

    public SearchDebugResponse debugSearch(QueryRequest request) {
        return aiEngineClient.debugSearch(request);
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
