package com.localrag.core;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.localrag.core.client.AiEngineClient;
import com.localrag.core.model.ChatSession;
import com.localrag.core.model.Citation;
import com.localrag.core.model.DocumentSummary;
import com.localrag.core.model.QueryRequest;
import com.localrag.core.model.QueryResponse;
import com.localrag.core.service.ChatSessionService;
import com.localrag.core.service.RagGatewayService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.codec.ServerSentEvent;
import reactor.core.publisher.Flux;
import reactor.test.StepVerifier;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

@SpringBootTest
class CoreServiceApplicationTests {

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void contextLoads() {
        assertThat(objectMapper).isNotNull();
    }

    @Test
    void chatSessionLifecycleAndStreamingPersistence() {
        AiEngineClient mockClient = mock(AiEngineClient.class);
        ChatSessionService sessionService = new ChatSessionService();
        RagGatewayService gatewayService = new RagGatewayService(mockClient, sessionService, objectMapper);

        Citation citation = new Citation(1, "doc-1", "architecture.md", 0, 1, "RAG uses LanceDB...", 0.92);
        when(mockClient.query(any())).thenReturn(new QueryResponse(
                "How does RAG work?",
                "RAG retrieves passages from LanceDB [1].",
                List.of(citation),
                12.5,
                210.0,
                "deepseek-r1:latest",
                null
        ));

        // 1. Standard query creates a session and stores 2 messages (user + assistant)
        QueryResponse response = gatewayService.query(new QueryRequest("How does RAG work?", 4, false, null));
        assertThat(response.sessionId()).isNotBlank();

        ChatSession session = sessionService.getSession(response.sessionId()).orElseThrow();
        assertThat(session.messages()).hasSize(2);
        assertThat(session.messages().get(0).role()).isEqualTo("user");
        assertThat(session.messages().get(1).role()).isEqualTo("assistant");
        assertThat(session.messages().get(1).citations()).hasSize(1);

        // 2. Streaming query appends to the existing session when stream completes
        Flux<String> simulatedStream = Flux.just(
                "{\"type\":\"citations\",\"citations\":[{\"citation_id\":1,\"document_id\":\"doc-1\",\"source_filename\":\"architecture.md\",\"chunk_index\":0,\"page_number\":1,\"snippet\":\"RAG...\",\"relevance_score\":0.95}]}",
                "{\"type\":\"token\",\"token\":\"Streaming \"}",
                "{\"type\":\"token\",\"token\":\"answer [1].\"}",
                "{\"type\":\"done\"}"
        );
        when(mockClient.streamQuery(any())).thenReturn(simulatedStream);

        Flux<ServerSentEvent<String>> sseFlux = gatewayService.streamQuery(
                new QueryRequest("Follow-up question", 4, true, session.id())
        );

        StepVerifier.create(sseFlux)
                .assertNext(event -> assertThat(event.data()).contains("\"type\":\"session\""))
                .expectNextCount(4)
                .verifyComplete();

        ChatSession updatedSession = sessionService.getSession(session.id()).orElseThrow();
        assertThat(updatedSession.messages()).hasSize(4);
        assertThat(updatedSession.messages().get(3).content()).isEqualTo("Streaming answer [1].");
        assertThat(updatedSession.messages().get(3).citations()).hasSize(1);

        // 3. Listing documents ingested prior to gateway startup (null fileSizeBytes) does not NPE
        when(mockClient.listDocuments()).thenReturn(List.of(
                new DocumentSummary("doc-preexisting", "python_asyncio.md", 3, null, null)
        ));
        List<DocumentSummary> docs = gatewayService.listDocuments();
        assertThat(docs).hasSize(1);
        assertThat(docs.get(0).fileSizeBytes()).isNull();
    }
}

