package com.localrag.core.controller;

import com.localrag.core.service.RagGatewayService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
public class HealthController {

    private final RagGatewayService gatewayService;

    public HealthController(RagGatewayService gatewayService) {
        this.gatewayService = gatewayService;
    }

    @GetMapping({"/health", "/api/v1/health"})
    public Map<String, Object> health() {
        return gatewayService.checkSystemHealth();
    }
}

