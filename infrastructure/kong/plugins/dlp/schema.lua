local typedefs = require "kong.db.schema.typedefs"

return {
  name = "dlp",
  fields = {
    { protocols = typedefs.protocols_http },
    {
      config = {
        type = "record",
        fields = {
          {
            block_pii = {
              type = "boolean",
              required = true,
              default = true,
            },
          },
          {
            block_injection = {
              type = "boolean",
              required = true,
              default = true,
            },
          },
          {
            audit_log_blocks = {
              type = "boolean",
              required = true,
              default = true,
            },
          },
        },
      },
    },
  },
}
