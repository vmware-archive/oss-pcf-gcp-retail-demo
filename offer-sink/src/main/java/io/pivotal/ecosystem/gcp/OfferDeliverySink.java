/**
 Copyright (C) 2017-Present Pivotal Software, Inc. All rights reserved.

 This program and the accompanying materials are made available under
 the terms of the under the Apache License, Version 2.0 (the "License”);
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 */

package io.pivotal.ecosystem.gcp;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cloud.stream.annotation.EnableBinding;
import org.springframework.cloud.stream.annotation.StreamListener;
import org.springframework.cloud.stream.messaging.Sink;

@EnableBinding(Sink.class)
public class OfferDeliverySink 
{
	private static final Logger LOG = LoggerFactory.getLogger(OfferDeliverySink.class);

	private OfferDeliveryService service;
	
	public OfferDeliverySink(OfferDeliveryService service)
	{
		this.service = service;
		LOG.debug("Constructor called. " + this.service);
	}
	
	@StreamListener(Sink.INPUT)
	public void process(String data) {
		LOG.debug("process received: " + data);
		service.deliver(data);
	}	

}
