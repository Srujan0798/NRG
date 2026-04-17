local cjson = require "cjson"
local ngx_re = require "ngx.re"

local DLPHandler = {}

DLPHandler.PRIORITY = 1000
DLPHandler.VERSION = "2.0.0"

-- Expanded PII patterns for IITGN security perimeter
local PII_PATTERNS = {
  aadhaar = {
    regex = "\\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\\b",
    block = true,
    tokenize = true,
    severity = "critical"
  },
  pan = {
    regex = "\\b[A-Z]{5}[0-9]{4}[A-Z]\\b",
    block = true,
    tokenize = false,
    severity = "critical"
  },
  phone = {
    regex = "\\b(?:\\+91|0)?[6-9][0-9]{9}\\b",
    block = true,
    tokenize = true,
    severity = "high"
  },
  passport = {
    regex = "\\b[A-Z][0-9]{7}\\b",
    block = true,
    tokenize = false,
    severity = "critical"
  },
  email = {
    regex = "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b",
    block = false,
    tokenize = true,
    severity = "medium"
  },
  upi_id = {
    regex = "\\b[a-zA-Z0-9._-]+@[a-zA-Z]{2,}\\b",
    block = true,
    tokenize = false,
    severity = "high"
  },
  ifsc = {
    regex = "\\b[A-Z]{4}0[A-Z0-9]{6}\\b",
    block = true,
    tokenize = false,
    severity = "critical"
  },
  driving_license = {
    regex = "\\b[A-Z]{2}[0-9]{2}[- ]?[0-9]{11}\\b",
    block = true,
    tokenize = false,
    severity = "high"
  },
  voter_id = {
    regex = "\\b[A-Z]{3}[0-9]{7}\\b",
    block = true,
    tokenize = false,
    severity = "high"
  }
}

-- Injection attack patterns
local INJECTION_PATTERNS = {
  "system\\s+prompt",
  "ignore\\s+previous",
  "as\\s+an\\s+ai",
  "you\\s+are\\s+now",
  "role\\s+play",
  "hypothetical",
  "disregard.*instructions",
  "from.*now.*on",
  "bypass.*security",
  "override.*protocol",
  "jailbreak",
  "prompt\\s+injection",
  "developer\\s+mode"
}

-- Tokenization helper (HMAC-based format preservation)
local function tokenize_value(value, pii_type)
  -- Get tokenization secret from Kong config
  local token_secret = ngx.var.DLP_TOKENIZATION_SECRET or "default-secret"
  
  local hmac = ngx.hmac_sha1(token_secret, value)
  local encoded = ngx.encode_base64(hmac)
  
  -- Preserve format: show last 4 chars
  local visible_chars = string.sub(value, -4)
  local masked = string.rep("*", string.len(value) - 4) .. visible_chars
  
  return {
    tokenized = "[TOKENIZED:" .. pii_type .. ":" .. string.sub(encoded, 1, 16) .. "...]",
    masked = masked
  }
end

-- Audit logging with enhanced metadata
local function audit_block(conf, block_reason, detected_type, severity)
  if not conf.audit_log_blocks then
    return
  end

  local request_id = kong.request.get_header("X-Request-ID") or "unknown"
  
  local payload = {
    event = "dlp_blocked",
    request_id = request_id,
    block_reason = block_reason,
    detected_type = detected_type,
    severity = severity or "high",
    client_ip = kong.client.get_forwarded_ip() or kong.client.get_ip(),
    client_user_agent = kong.request.get_header("User-Agent") or "unknown",
    path = kong.request.get_path(),
    method = kong.request.get_method(),
    timestamp = ngx.utctime()
  }

  kong.log.set_serialize_value("dlp.blocked", true)
  kong.log.set_serialize_value("dlp.block_reason", block_reason)
  kong.log.set_serialize_value("dlp.detected_type", detected_type)
  kong.log.set_serialize_value("dlp.severity", severity)
  kong.log.notice(cjson.encode(payload))
end

-- Tokenization audit log
local function audit_tokenize(conf, detected_type, original_length)
  if not conf.audit_log_tokenized then
    return
  end

  local request_id = kong.request.get_header("X-Request-ID") or "unknown"
  
  local payload = {
    event = "dlp_tokenized",
    request_id = request_id,
    detected_type = detected_type,
    original_length = original_length,
    client_ip = kong.client.get_forwarded_ip() or kong.client.get_ip(),
    timestamp = ngx.utctime()
  }

  kong.log.set_serialize_value("dlp.tokenized", true)
  kong.log.set_serialize_value("dlp.tokenized_type", detected_type)
  kong.log.info(cjson.encode(payload))
end

-- Block request with standardized error response
local function block_request(conf, block_reason, message, detected_type, severity, status_code)
  audit_block(conf, block_reason, detected_type, severity)

  return kong.response.exit(status_code or 400, {
    error = block_reason,
    message = message,
    detected_type = detected_type,
    severity = severity,
    request_id = kong.request.get_header("X-Request-ID")
  })
end

-- Tokenize and allow request (PII masked)
local function tokenize_and_pass(conf, query, detected_type, pattern_config)
  local tokenized = tokenize_value(query, detected_type)
  audit_tokenize(conf, detected_type, string.len(query))
  
  return {
    query = query,
    tokenized_query = tokenized.masked,
    warnings = {"PII detected and tokenized: " .. detected_type}
  }
end

function DLPHandler:access(conf)
  ngx.req.read_body()
  local body = kong.request.get_body()

  if body and conf.block_pii then
    -- Check query body parameter
    if type(body.query) == "string" then
      local query = body.query

      -- Use expanded PII_PATTERNS from module scope
      for pii_type, pattern_config in pairs(PII_PATTERNS) do
        local matches = ngx.re.match(query, pattern_config.regex, "ijo")
        if matches then
          -- Block critical/high severity PII
          if pattern_config.block and (pattern_config.severity == "critical" or pattern_config.severity == "high") then
            return block_request(
              conf,
              "DLP_VIOLATION",
              "PII detected in query: " .. pii_type,
              pii_type,
              pattern_config.severity,
              400
            )
          -- Tokenize medium severity (email)
          elseif pattern_config.tokenize and pattern_config.severity == "medium" then
            local tokenized = tokenize_and_pass(conf, query, pii_type, pattern_config)
            -- Set headers for downstream processing
            kong.service.request.set_header("X-DLP-Tokenized", "true")
            kong.service.request.set_header("X-DLP-Type", pii_type)
          end
        end
      end
    end
    
    -- Also check nested query in JSON body
    if type(body.query) == "string" then
      local query = body.query
      
      for pii_type, pattern_config in pairs(PII_PATTERNS) do
        local matches = ngx.re.match(query, pattern_config.regex, "ijo")
        if matches and pattern_config.block then
          return block_request(
            conf,
            "DLP_VIOLATION",
            "PII detected in query: " .. pii_type,
            pii_type,
            pattern_config.severity,
            400
          )
        end
      end
    end
  end

  if body and conf.block_injection then
    if type(body.query) == "string" then
      local query = body.query

      -- Use expanded INJECTION_PATTERNS from module scope
      for _, pattern in ipairs(INJECTION_PATTERNS) do
        if ngx.re.match(query, pattern, "ijo") then
          return block_request(
            conf,
            "PROMPT_INJECTION",
            "Potential prompt injection detected",
            "injection_attempt",
            "critical",
            400
          )
        end
      end
    end
  end
end

return DLPHandler
