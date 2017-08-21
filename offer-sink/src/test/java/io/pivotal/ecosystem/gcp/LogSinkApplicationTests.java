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

package io.pivotal.ecosystem.gcp;

import static org.junit.Assert.assertNotNull;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.Resource;
import org.springframework.test.context.junit4.SpringRunner;

@RunWith(SpringRunner.class)
@SpringBootTest
public class LogSinkApplicationTests 
{
	private static final Logger LOG = LoggerFactory.getLogger(LogSinkApplicationTests.class);

	@Autowired 
	private OfferDeliveryService service;
	
	@Test
	public void contextLoads() 
	{
		LOG.debug("service = " + service);
		assertNotNull(service);
		
		Resource resource = new ClassPathResource("/message1.json");
		try
		{
			String content = new String(Files.readAllBytes(Paths.get(resource.getURI())));
			assertNotNull(content);
			service.deliver(content);
		}
		catch (IOException e)
		{
			LOG.error("Error reading json file", e);
		}
	}

}
