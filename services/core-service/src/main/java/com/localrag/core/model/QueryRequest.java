package com.localrag.core.model;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import jakarta.validation.constraints.NotBlank;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public record QueryRequest(
        @NotBlank(message = "Query must not be blank")
        String query,
        Integer topK,
        Boolean stream,
        String sessionId
) {}

