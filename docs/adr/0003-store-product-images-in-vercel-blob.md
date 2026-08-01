# Store product images in Vercel Blob

Product images will be optional public objects stored in Vercel Blob and uploaded through the FastAPI application, with PostgreSQL retaining the blob reference. JPEG, PNG, and WebP files up to 5 MB are accepted; replacing or removing an image manages the corresponding object lifecycle, while products without one use a generic image bundled with the frontend. This keeps binary data out of PostgreSQL and preserves the API boundary at the cost of coupling image storage to Vercel.
