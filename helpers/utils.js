"use strict";
module.exports = {
  exec: function(command, options, callback) {
    const {
      spawn
    } = require('child_process');

    // console.log(command+" "+options);
    const pyProg = spawn(command, options);
    pyProg.stdout.on('data', callback);
    pyProg.stderr.on('data', callback);
    pyProg.on('close', callback);
  }
}
