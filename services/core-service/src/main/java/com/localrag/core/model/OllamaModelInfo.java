package com.localrag.core.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public record OllamaModelInfo(
        @JsonProperty("name") String name,
        @JsonProperty("size") long size,
        @JsonProperty("modified_at") String modifiedAt,
        @JsonProperty("details") ModelDetails details
) {}
