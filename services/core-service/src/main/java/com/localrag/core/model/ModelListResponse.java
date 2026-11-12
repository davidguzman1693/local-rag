package com.localrag.core.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public record ModelListResponse(
        @JsonProperty("models") List<OllamaModelInfo> models,
        @JsonProperty("current_default") String currentDefault
) {}
