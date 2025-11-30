# TestProject
## README.md
# Test Project

Ceci est un projet de test pour FileGen.

## index.js
const message = "Hello from test project";
console.log(message);

## package.json
{
  "name": "test-project",
  "version": "1.0.0",
  "main": "index.js"
}

# TestProject/src
## app.js
// Application principale
function main() {
  console.log("App started");
}

main();

## config.js
module.exports = {
  port: 3000,
  env: "test"
};

# TestProject/src/utils
## helpers.js
function formatDate(date) {
  return date.toISOString();
}

module.exports = { formatDate };

## validation.js
function isValid(input) {
  return input !== null && input !== undefined;
}

module.exports = { isValid };

# TestProject/tests
## test_app.js
const assert = require('assert');

describe('App', () => {
  it('should start', () => {
    assert.ok(true);
  });
});