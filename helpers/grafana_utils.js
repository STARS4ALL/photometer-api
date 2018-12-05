module.exports = {
  parseAuth: function(token) {
    const strauth = new Buffer(token, 'base64').toString();
    const splitIndex = strauth.indexOf(':');
    return [strauth.substring(0, splitIndex), strauth.substring(splitIndex + 1)]
  },
  isAdmin: function(orgs) {
    let filterOrg = orgs.filter(org => {
      return org.name === "Main Org." && org.role === "Admin";
    });
    return filterOrg.length;
  },
  isAdminRolAsync: function(token, callback) {
    var config = require('../config.js');
    var auth = this.parseAuth(token);
    var url = `http://${encodeURI(auth[0])}:${encodeURI(auth[1])}@${GRAFANA_HOST}/api/user/orgs`;
    var request = require('request');
    request.get({
      url: url
    }, function(error, response, body) {
      var result = JSON.parse(body);

      if ("message" in result) {
        callback({
          error: result["message"]
        });
      } else if (require('./grafana_utils').isAdmin(result)) {
        callback({
            success: true
        });
      } else {
        callback({
          error: "No Admin Role"
        });
      }
    });
  }
}
