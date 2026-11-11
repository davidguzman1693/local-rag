package com.localrag.core.client;

import com.localrag.core.model.ChunkRecord;
import com.localrag.core.model.DocumentSummary;
import com.localrag.core.model.IngestResponse;
import com.localrag.core.model.QueryRequest;
import com.localrag.core.model.QueryResponse;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Flux;

import java.io.IOException;
import java.util.List;
import java.util.Map;

@Component
public class AiEngineClient {

    private final WebClient webClient;

    public AiEngineClient(WebClient aiServiceWebClient) {
        this.webClient = aiServiceWebClient;
    }

    public Map<String, Object> checkHealth() {
        try {
            return webClient.get()
                    .uri("/health")
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                    .block();
        } catch (Exception e) {
            return Map.of(
                    "status", "unreachable",
                    "error", e.getMessage() != null ? e.getMessage() : "Connection refused"
            );
        }
    }

    public IngestResponse uploadDocument(MultipartFile file) {
        try {
            byte[] bytes = file.getBytes();
            String filename = file.getOriginalFilename() != null ? file.getOriginalFilename() : "document.txt";

            MultipartBodyBuilder builder = new MultipartBodyBuilder();
            builder.part("file", new ByteArrayResource(bytes) {
                        @Override
                        public String getFilename() {
                            return filename;
                        }
                    })
                    .contentType(MediaType.APPLICATION_OCTET_STREAM);

            return webClient.post()
                    .uri("/api/v1/documents/upload")
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(BodyInserters.fromMultipartData(builder.build()))
                    .retrieve()
                    .bodyToMono(IngestResponse.class)
                    .block();
        } catch (IOException e) {
            throw new AiServiceException("Failed to read uploaded file bytes: " + e.getMessage(), e);
        } catch (WebClientResponseException e) {
            throw new AiServiceException("AI Engine failed to ingest document: " + e.getResponseBodyAsString(), e.getStatusCode());
        } catch (Exception e) {
            throw new AiServiceException("Error communicating with AI Engine during upload: " + e.getMessage(), e);
        }
    }

    public List<DocumentSummary> listDocuments() {
        try {
            return webClient.get()
                    .uri("/api/v1/documents")
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<List<DocumentSummary>>() {})
                    .block();
        } catch (WebClientResponseException e) {
            throw new AiServiceException("Failed to list documents from AI Engine: " + e.getResponseBodyAsString(), e.getStatusCode());
        } catch (Exception e) {
            throw new AiServiceException("Error communicating with AI Engine: " + e.getMessage(), e);
        }
    }

    public List<ChunkRecord> getDocumentChunks(String documentId) {
        try {
            return webClient.get()
                    .uri("/api/v1/documents/{documentId}/chunks", documentId)
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<List<ChunkRecord>>() {})
                    .block();
        } catch (WebClientResponseException e) {
            throw new AiServiceException("Failed to fetch chunks for document " + documentId + ": " + e.getResponseBodyAsString(), e.getStatusCode());
        } catch (Exception e) {
            throw new AiServiceException("Error communicating with AI Engine: " + e.getMessage(), e);
        }
    }

    public Map<String, Object> deleteDocument(String documentId) {
        try {
            return webClient.delete()
                    .uri("/api/v1/documents/{documentId}", documentId)
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                    .block();
        } catch (WebClientResponseException e) {
            throw new AiServiceException("Failed to delete document " + documentId + ": " + e.getResponseBodyAsString(), e.getStatusCode());
        } catch (Exception e) {
            throw new AiServiceException("Error communicating with AI Engine: " + e.getMessage(), e);
        }
    }

    public QueryResponse query(QueryRequest request) {
        try {
            Map<String, Object> payload = request.topK() != null
                    ? Map.of("query", request.query(), "top_k", request.topK(), "stream", false)
                    : Map.of("query", request.query(), "stream", false);

            return webClient.post()
                    .uri("/api/v1/query")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(payload)
                    .retrieve()
                    .bodyToMono(QueryResponse.class)
                    .block();
        } catch (WebClientResponseException e) {
            throw new AiServiceException("AI Engine query failed: " + e.getResponseBodyAsString(), e.getStatusCode());
        } catch (Exception e) {
            throw new AiServiceException("Error communicating with AI Engine: " + e.getMessage(), e);
        }
    }

    public Flux<String> streamQuery(QueryRequest request) {
        Map<String, Object> payload = request.topK() != null
                ? Map.of("query", request.query(), "top_k", request.topK(), "stream", true)
                : Map.of("query", request.query(), "stream", true);

        return webClient.post()
                .uri("/api/v1/query/stream")
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.TEXT_EVENT_STREAM)
                .bodyValue(payload)
                .retrieve()
                .bodyToFlux(String.class);
    }
}

