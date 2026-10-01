// Test-only observation of the SDK's actual read; no body or credentials leave the page.
export async function observeApiBodies(page, consumed) {
  await page.exposeFunction('__ossfApiBodyConsumed', consumed);
  await page.addInitScript(() => {
    const fetch = globalThis.fetch.bind(globalThis);
    globalThis.fetch = async (...args) => {
      const began = performance.now();
      const response = await fetch(...args);
      const path = new URL(response.url).pathname;
      if (!path.startsWith('/v1/') || !response.body) return response;
      const headerSeconds = (performance.now() - began) / 1000;
      const method = args[1]?.method ?? (args[0] instanceof Request ? args[0].method : 'GET');
      const body = response.body, getReader = body.getReader.bind(body);
      Object.defineProperty(body, 'getReader', {value: (...readerArgs) => {
        const reader = getReader(...readerArgs), read = reader.read.bind(reader);
        let recorded = false;
        Object.defineProperty(reader, 'read', {value: async (...readArgs) => {
          const result = await read(...readArgs);
          if (result.done && !recorded) {
            recorded = true;
            await globalThis.__ossfApiBodyConsumed({path, method, status: response.status,
              cache: response.headers.get('cache-control'), header_seconds: headerSeconds,
              body_seconds: (performance.now() - began) / 1000});
          }
          return result;
        }});
        return reader;
      }});
      return response;
    };
  });
}
