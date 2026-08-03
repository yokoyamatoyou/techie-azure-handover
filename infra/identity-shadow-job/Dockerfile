# Intentionally no defaults. Docker's digest-reference grammar makes an
# unpinned base fail before FROM resolves.
ARG NODE_BASE_IMAGE_REPOSITORY
ARG NODE_BASE_IMAGE_DIGEST
FROM ${NODE_BASE_IMAGE_REPOSITORY}@${NODE_BASE_IMAGE_DIGEST}

WORKDIR /app
ENV NODE_ENV=production

COPY identity-shadow-job/package.json identity-shadow-job/package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts \
    && npm cache clean --force

COPY 20260804_identity_shadow_probe.js ./

USER node
ENTRYPOINT ["node", "/app/20260804_identity_shadow_probe.js", "--expect-empty"]
