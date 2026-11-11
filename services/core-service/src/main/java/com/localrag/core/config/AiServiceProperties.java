package com.localrag.core.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "local-rag.ai-service")
public record AiServiceProperties(
        String baseUrl,
        int timeoutSeconds
) {
    public AiServiceProperties {
        if (baseUrl == null || baseUrl.isBlank()) {
            baseUrl = "http://127.0.0.1:8000";
        }
        if (timeoutSeconds <= 0) {
            timeoutSeconds = 120;
        }
    }
}

