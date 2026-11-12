package com.localrag.core.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;

@JsonIgnoreProperties(ignoreUnknown = true)
public record QueryRequest(
        @NotBlank(message = "Query must not be blank")
        @JsonProperty("query") String query,
        @JsonProperty("top_k") Integer topK,
        @JsonProperty("stream") Boolean stream,
        @JsonProperty("session_id") String sessionId,
        @JsonProperty("model") String model,
        @JsonProperty("temperature") Double temperature
) {
    public QueryRequest(String query, Integer topK, Boolean stream, String sessionId) {
        this(query, topK, stream, sessionId, null, null);
    }
}

