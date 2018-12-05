module.exports = {
  parseMAC: function(tess_mac) {
    if (!tess_mac)return tess_mac;
    
    var mac = tess_mac.replace(/[^a-zA-Z0-9]/g, '');
    if (mac.length !== 12) {
      return null;
    }
    return mac.match(new RegExp('.{2}', 'g')).join(':');
  },
  cleanTess: function(tess) {
    const removeEmpty = (obj) => {
      const o = JSON.parse(JSON.stringify(obj)); // Clone source oect.

      Object.keys(o).forEach(key => {
        if (o[key] && typeof o[key] === 'object')
          o[key] = removeEmpty(o[key]); // Recurse.
        else if (o[key] === undefined || o[key] === null || o[key] === '')
          delete o[key]; // Delete undefined and null.
        else
          o[key] = o[key]; // Copy value.
      });

      return o; // Return new object.
    };
    console.log(removeEmpty(tess))
    return removeEmpty(tess);
  }


}
