# Google Places address autocomplete

The public quote form reads the browser Maps key from the `GOOGLE_MAPS_API_KEY`
environment variable. Add the key to the web app's environment configuration to
enable Google Places suggestions. If it is absent, the address field remains
available for manual entry.

The key is sent to the browser because the Maps JavaScript API runs client-side.
Create a dedicated key, enable the Maps JavaScript API and Places API (New), and
restrict the key to the production site's HTTP referrers and only the APIs used
by this form. Google Maps Platform requires a billing-enabled Cloud project.

The autocomplete is limited to France. After a result is selected, the form
fills the venue/street address, city, and postal code; users can still edit the
filled fields before submitting.
