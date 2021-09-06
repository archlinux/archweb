# Mirror Access

Archweb can be used as external authentication provider in combination with
[ngx_http_auth_request_module](http://nginx.org/en/docs/http/ngx_http_auth_request_module.html).
A user with a Developer, Trusted User and Support Staff role can generate an
access token used in combination with his username on the `/devel/tier0mirror`
url. The mirror authentication is done against `/devel/mirrorauth` using HTTP
Basic authentication.

## Configuration

There are two configuration options for this feature of which one is optional:

* **TIER0_MIRROR_DOMAIN** - the mirror domain used to display the mirror url with authentication.
* **TIER0_MIRROR_SECRET** - an optional secret send by nginx in the `X-Sent-From` header, all requests without this secret value are ignored. This can be used to not allow anyone to bruteforce guess the http basic auth pass/token.

## nginx configuration

Example configuration with optional caching of the authentication request to
reduce hammering archweb when for example using this feature for a mirror. By
default archweb caches `/devel/mirrorauth` for 5 minutes.

```
http {
    proxy_cache_path  /var/lib/nginx/cache/auth_cache levels=1:2 keys_zone=auth_cache:5m;

    server {
        location /protected {
                auth_request /devel/mirrorauth;

                root   /usr/share/nginx/html;
                index  index.html index.htm;
        }

        location = /devel/mirrorauth {
            internal;

            # Do not pass the request body, only http authorisation header is required
            proxy_pass_request_body off;
            proxy_set_header        Content-Length "";

            # Proxy headers
            proxy_set_header        Host                    $host;
            proxy_set_header        X-Original-URL          $scheme://$http_host$request_uri;
            proxy_set_header        X-Original-Method       $request_method;
            proxy_set_header        X-Auth-Request-Redirect $request_uri;
            proxy_set_header        X-Sent-From             "arch-nginx";

            # Cache responses from the auth proxy
            proxy_cache             auth_cache;
            proxy_cache_key         "$scheme$proxy_host$request_uri$http_authorization";

            # Authentication to archweb
            proxy_pass https://archlinux.org;
        }
    }
}
```
