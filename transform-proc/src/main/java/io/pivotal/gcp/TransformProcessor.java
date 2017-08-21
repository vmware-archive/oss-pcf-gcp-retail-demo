/**
 * Copyright (C) 2017-Present Pivotal Software, Inc. All rights reserved.
 * <p>
 * This program and the accompanying materials are made available under
 * the terms of the under the Apache License, Version 2.0 (the "License”);
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * <p>
 * http://www.apache.org/licenses/LICENSE-2.0
 * <p>
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package io.pivotal.gcp;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategy;
import io.pivotal.gcp.domain.MockSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.stream.annotation.EnableBinding;
import org.springframework.cloud.stream.messaging.Processor;
import org.springframework.http.*;
import org.springframework.http.converter.json.MappingJackson2HttpMessageConverter;
import org.springframework.integration.annotation.ServiceActivator;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

@EnableBinding(Processor.class)
public class TransformProcessor {

    private final DateTimeFormatter dtFormat = DateTimeFormatter.ofPattern("MM/dd/yy HH:mm:ss");
    private ObjectMapper mapper;
    private String dsAppUrl;
    private boolean dsAppAvailable = true;

    // NOTE: service-name is set at SCDF stream create time, in ../scdf/scdf_create_stream.sh
    @Autowired
    public TransformProcessor(@Value("${vcap.services.${service-name}.credentials.uri}") String dsAppUrl) {
        this.dsAppUrl = dsAppUrl;
        System.out.println("dsAppUrl: " + dsAppUrl);
        mapper = new ObjectMapper();
        mapper.setPropertyNamingStrategy(PropertyNamingStrategy.SNAKE_CASE);
    }

    @ServiceActivator(inputChannel = Processor.INPUT, outputChannel = Processor.OUTPUT)
    public Object transform(Object payload) {
        System.out.println("TransformProcessor, payload => \"" + payload + "\"");
        payload = runDataScience(payload.toString());
        System.out.println("TransformProcessor, transformed result => \"" + payload + "\"");
        return payload;
    }

    /*
     * Send the JSON object off to the Data Science Interrogator app and receive the JSON response.
     * If that service is not available, this is a no-op and returns the original JSON.
     */
    private String runDataScience(String json) {
        // FIXME: Use Circuit Breaker (https://spring.io/guides/gs/circuit-breaker/)
        dsAppAvailable = true;
        if (dsAppAvailable) {
            RestTemplate restTemplate = new RestTemplate();
            restTemplate.getMessageConverters().add(new MappingJackson2HttpMessageConverter());
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<String> entity = new HttpEntity<>(json, headers);
            try {
                ResponseEntity<String> response = restTemplate.exchange(dsAppUrl, HttpMethod.POST, entity, String.class);
                json = response.getBody();
            } catch (Exception e) {
                dsAppAvailable = false;
                System.out.println("Data Science App Unavailable at " + dsAppUrl);
            }
        }
        return json;
    }

}
