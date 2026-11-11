package com.localrag.core.model;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

import java.time.Instant;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public record DocumentSummary(
        String documentId,
        String sourceFilename,
        int chunkCount,
        Long fileSizeBytes,
        Instant uploadedAt
) {}

