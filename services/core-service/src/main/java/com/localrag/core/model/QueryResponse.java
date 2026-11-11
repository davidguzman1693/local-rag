package com.localrag.core.model;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

import java.util.List;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public record QueryResponse(
        String query,
        String answer,
        List<Citation> citations,
        double retrievalTimeMs,
        double totalTimeMs,
        String modelUsed,
        String sessionId
) {
    public QueryResponse withSessionId(String newSessionId) {
        return new QueryResponse(
                this.query,
                this.answer,
                this.citations,
                this.retrievalTimeMs,
                this.totalTimeMs,
                this.modelUsed,
                newSessionId
        );
    }
}

