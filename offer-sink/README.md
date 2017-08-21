# Log sink for inclusion in SCDF stream

## Prior to running the build on this project, do the following:
1. in `../twitter/`, ensure you have pushed the twitter app (e.g. `cf push` in that directory)
1. Edit `../twitter/scripts/cf_create_twitter_service.sh` as required, then run that
1. Once that service is created, bind it to a running app, so you can run `cf env [that app name]` to get the `VCAP_SERVICES`
   value out, and store that in an environment variable (`VCAP_SERVICES`)
1. After you're deployed the SCDF stream where this `offer-sink` app is a sink:
* Bind the app to the delivery service `cf bs dataflow-server-hf30QYI-socialmedia-offer-sink twitter-service`
* Restage the app so that binding takes effect `cf restage dataflow-server-hf30QYI-socialmedia-offer-sink`

## TODO
Remove the Twitter specific parts of this, as it doesn't currently handle the Twitter interactions.

