package com.localrag.core.controller;

import com.localrag.core.model.ModelListResponse;
import com.localrag.core.service.RagGatewayService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/models")
public class ModelController {

    private final RagGatewayService gatewayService;

    public ModelController(RagGatewayService gatewayService) {
        this.gatewayService = gatewayService;
    }

    @GetMapping
    public ModelListResponse listModels() {
        return gatewayService.listModels();
    }
}

