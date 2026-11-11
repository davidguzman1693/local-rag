package com.localrag.core.controller;

import com.localrag.core.model.ChunkRecord;
import com.localrag.core.model.DocumentSummary;
import com.localrag.core.model.IngestResponse;
import com.localrag.core.service.RagGatewayService;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/documents")
public class DocumentController {

    private final RagGatewayService gatewayService;

    public DocumentController(RagGatewayService gatewayService) {
        this.gatewayService = gatewayService;
    }

    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public IngestResponse uploadDocument(@RequestParam("file") MultipartFile file) {
        return gatewayService.uploadDocument(file);
    }

    @GetMapping
    public List<DocumentSummary> listDocuments() {
        return gatewayService.listDocuments();
    }

    @GetMapping("/{documentId}/chunks")
    public List<ChunkRecord> getDocumentChunks(@PathVariable String documentId) {
        return gatewayService.getDocumentChunks(documentId);
    }

    @DeleteMapping("/{documentId}")
    public Map<String, Object> deleteDocument(@PathVariable String documentId) {
        return gatewayService.deleteDocument(documentId);
    }
}

