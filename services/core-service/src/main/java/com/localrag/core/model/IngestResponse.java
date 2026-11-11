package com.localrag.core.model;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public record IngestResponse(
        String documentId,
        String filename,
        int chunksCreated,
        String message
) {}

