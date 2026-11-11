package com.localrag.core.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;

import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public record ChunkRecord(
        String id,
        String text,
        String documentId,
        String sourceFilename,
        int chunkIndex,
        int charStart,
        int charEnd,
        int pageNumber,
        List<Float> vector
) {}

