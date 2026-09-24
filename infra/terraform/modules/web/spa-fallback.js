// The SPA fallback, at the edge, on the viewer request.
//
// This is what `app/main.py` does for the single-process arrangement -- every
// non-API URL returns the identical shell and React Router decides what to
// render -- and what S3 cannot do at all, because a deep link is a key that does
// not exist.
//
// It runs as a CloudFront Function rather than as a `custom_error_response`
// because an error response is a member of the DISTRIBUTION and a function
// association is a member of a BEHAVIOUR. The distribution-wide form rewrote
// every 403 and 404 in front of both origins, including the API's own refusals;
// this one is attached to the S3 behaviour in `main.tf` and the `/api/*`
// behaviour never invokes it.
//
// A rewrite, not a redirect: the viewer's URL stays the deep link it typed, and
// the router reads it on the way in.
//
// Runtime `cloudfront-js-2.0`. There is no `require`, no network and no state:
// a CloudFront Function gets about a millisecond and is charged accordingly.
function handler(event) {
    var request = event.request;
    var uri = request.uri;

    // Belt and braces. The API has its own cache behaviour, so this function is
    // never invoked for it -- but that is a property of a configuration file
    // this function cannot see, and the whole defect being fixed here was a
    // rule that held everywhere except where somebody assumed it did.
    //
    // `event.request.uri` carries the leading slash, unlike the `full_path`
    // that Starlette hands the same guard in `app/main.py`.
    if (uri.startsWith('/api/')) {
        return request;
    }

    // A hashed bundle that is missing must arrive as missing. Publication is
    // additive now (`scripts/deploy.sh` step 5 deletes nothing), so a bundle
    // `index.html` names is no longer removed by the next release -- but "no
    // longer removed by a deploy" is not "cannot be absent": a bucket restored
    // by hand, a lifecycle rule somebody adds, a partial upload. Answering that
    // with the shell turns a failed module load into a blank screen and an empty
    // log; answering it with a 404 turns it into a line in the browser's console
    // that says which file.
    if (uri.startsWith('/assets/')) {
        return request;
    }

    // A navigation is a path whose last segment has no extension: `/entries`,
    // `/entries/0f8c...`, `/` (which is the empty segment). Anything with a dot
    // is a file that either exists in the bucket or does not, and both of those
    // are answers.
    if (uri.substring(uri.lastIndexOf('/') + 1).indexOf('.') === -1) {
        request.uri = '/index.html';
    }

    return request;
}
