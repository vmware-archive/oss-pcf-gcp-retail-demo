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

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.List;

@Service
public class OfferDeliveryService
{
	private static final Logger LOG = LoggerFactory.getLogger(OfferDeliveryService.class);

	private static final String USER = "user";
	private static final String SCREEN_NAME = "screen_name";
	private static final String MAKE_OFFER = "make_offer";
	private static final String OFFER_ID = "offer_id";
	private static final String OFFER_TEXT = "offer_text";

	private final String twitterServiceUri;
	private final RestTemplate restTemplate;

	@Autowired
	public OfferDeliveryService(@Value("${vcap.services.twitter-service.credentials.uri}") String twitterServiceUri)
	{
		this.twitterServiceUri = twitterServiceUri;
		this.restTemplate = new RestTemplate();
	}

	// TODO: Move this into TwitterDeliverService
	public boolean tweet(Offer offer) {
		RestTemplate restTemplate = new RestTemplate();
		ResponseEntity<String> resp = restTemplate.postForEntity(twitterServiceUri, offer, String.class);
		HttpStatus status = resp.getStatusCode();
		LOG.debug("Offer tweet returned: " + resp.getBody());
		return status.is2xxSuccessful();
	}

	public void deliver(String message)
	{
		LOG.debug("deliver called with message : " + message);

		try
		{
			JSONObject json = new JSONObject(message);
			//String text = json.getString(TEXT);

			JSONObject user = json.getJSONObject(USER);
			String screenName = user.getString(SCREEN_NAME);
			LOG.debug("screenName = " + screenName);

			boolean makeOffer = false;
			if (json.has(MAKE_OFFER)) {
				makeOffer = json.getBoolean(MAKE_OFFER);
			}
			LOG.debug("makeOffer = " + makeOffer);

			/*
			 * MIKE: here, look for 'source' and, if it's twitter, get the twitter delivery
			 * endpoint and fire it off using that.
			 */
			if (makeOffer) {

				JSONArray offerItems = json.getJSONArray("offer_items");
				List<String> urlList = new ArrayList<>();
				for (int i = 0; i < offerItems.length(); i++) {
					urlList.add(offerItems.getJSONObject(i).getString("url"));
				}

				// Required to reply to a tweet
				long statusId = json.getLong("id");

				Offer offer = new Offer();
				offer.setOfferId(json.getString(OFFER_ID));
				offer.setOfferText(json.getString(OFFER_TEXT));
				offer.setUserId(screenName);
				offer.setUrlList(urlList);
				offer.setStatusId(statusId);
				boolean sent = tweet(offer);
				if (!sent) {
					LOG.error("Could not deliver offer!");
				}
			}

		} catch (JSONException e)
		{
			LOG.error("Error parsing inbound message " + message, e);
		}
	}
}
