package com.localrag.core.controller;

import com.localrag.core.model.QueryRequest;
import com.localrag.core.model.QueryResponse;
import com.localrag.core.model.SearchDebugResponse;
import com.localrag.core.service.RagGatewayService;
import jakarta.validation.Valid;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

@RestController
@RequestMapping("/api/v1/query")
public class QueryController {

    private final RagGatewayService gatewayService;

    public QueryController(RagGatewayService gatewayService) {
        this.gatewayService = gatewayService;
    }

    @PostMapping
    public QueryResponse query(@Valid @RequestBody QueryRequest request) {
        return gatewayService.query(request);
    }

    @PostMapping("/debug")
    public SearchDebugResponse debugSearch(@Valid @RequestBody QueryRequest request) {
        return gatewayService.debugSearch(request);
    }

    @PostMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<String>> streamQuery(@Valid @RequestBody QueryRequest request) {
        return gatewayService.streamQuery(request);
    }
}

