'use strict';

const express = require('express');
const mongoose = require('mongoose');
const bodyParser = require('body-parser');


//Import mongodb models
var Tess = require('./models/tess.js').Tess;
var Observations = require('./models/observation.js').Observations;
var Last = require('./models/observation.js').last_observations;
var Report = require('./models/report.js').Report;
var config = require('./config.js');
//var Crowd = require('./models/crowdstats.js').CrowdStats;

const PORT = 8888;

//DB Models
/*
 mongoose.connect(DATABASE_HOST + DATABASE_NAME, function (err, res) {

 if (err) {
 console.log('ERROR: connecting with db ' + err + ' ' + res);
 }
 });

 */

//Set up default mongoose connection
var mongoDB = DATABASE_HOST + DATABASE_NAME;
mongoose.Promise = require('bluebird');
mongoose.connect(mongoDB, {
  useMongoClient: true
});

var db = mongoose.connection;
db.on('error', console.error.bind(console, 'connection error:'));
db.once('open', function callback() {
  console.log('Connected to DB');
});


//App

var app = express();

//app.use(bodyParser.urlencoded({ extended:true }));
app.use(bodyParser.json());
app.use(function(req, res, next) {
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
  next();
});

var router = express.Router();

router.get('/', function(req, res) {
  res.json({
    message: 'Hello world\n'
  });
});

router.get('/info', function(req, res) {
  res.json({
    project: 'STARS4ALL',
    description: 'This is a REST API to access to the photometers data',
    funded: ' By European Union ( H2020 framework -> 688135)'
  });
});

//router.get('/crowdsourcing', function (req, res){
//
//	var beginInterval = req.query.begin;
//	var endInterval = req.query.end;
//	var project = req.query.project;
//
//	var query;
//
//	if ((beginInterval!=null) && (endInterval!=null)){
//		query = {date: {$gt: beginInterval, $lt: endInterval}};
//	} else if ((beginInterval!=null) && (endInterval==null)){
//		query = {date: {$gt : beginInterval}};
//	} else{
//		query = {};
//	}
//
//	if (project!=null){
//		query["project"]=project;
//	}
//
//	Crowd.find(query, function (errs,docs){
//		res.json(docs);
//	});
//});
/**
 * Lis of all photometers witout sensitive information
 * @param  {[type]} req [description]
 * @param  {[type]} res [description]
 * @return {[type]}     All Tess information
 */
router.get('/photometers', function(req, res) {

  Tess.find({}, {
    '_id': 0,
    'mac': 0,
    'info_contact': 0
  }, function(errs, docs) {
    res.json(docs);
  });

});

/**
 * Get photometer info
 * @param  {[type]} req [description]
 * @param  {[type]} res [description]
 * @return {json}     Tess information
 */
router.get('/photometers/:id', function(req, res) {

  Tess.findOne({
    name: req.params.id
  }, {
    '_id': 0,
    'mac': 0,
    'info_contact': 0
  }, function(errs, docs) {

    if (req.query.pretty) {
      res.json(JSON.stringify(docs, null, 4));
    } else {
      res.json(docs);
    }
  });

});

//******************************************************************************
/**
 * This is used to "login" as the owner of Tess
 * @param  {[type]} req [description]
 * @param  {[type]} res [description]
 * @return {json}     Tess information
 */
router.get('/photometers/:id/:mac', function(req, res) {
  var photometerUtils = require('./helpers/photometer_utils');
  var mac = photometerUtils.parseMAC(req.params.mac);
  if (!mac) {
    res.status(401);
    res.header('Tess_error', 'error_invalid_mac');
    res.send('error_invalid_mac');
    return;
  }

  var mac_reg = new RegExp(mac + '$', 'i');

  Tess.findOne({
    name: req.params.id,
    mac: mac_reg
  }, {
    '_id': 0
  }, function(errs, docs) {

    if (req.query.pretty) {
      res.json(JSON.stringify(docs, null, 4));
    } else {
      res.json(docs);
    }
  });
});

/**
 * Update tess info
 * @param  {[type]} req [description]
 * @param  {[type]} res [description]
 * @return {json}     Tess information
 */
router.post('/photometers/:id/:mac*?', function(req, res) {
  var photometerUtils = require('./helpers/photometer_utils');
  var mac = photometerUtils.parseMAC(req.params.mac);
  if (!mac && req.params.mac) {
    res.status(400);
    res.header('Tess_error', 'error_invalid_mac');
    res.send('error_invalid_mac');
    return;
  }

  var mac_reg = req.params.mac ? new RegExp(mac + '$', 'i') : '';

  var query = {
    name: req.params.id,
    mac: mac_reg
  };


  var tess_info = req.body.tess;

  if (!tess_info) {
    res.status(400);
    res.header('Tess_error', 'error_invalid_tess_info');
    res.send('error_invalid_tess_info');
    return;
  }

  var isNew = false;

  delete tess_info["_id"];

  function _update(_tess) {
    _tess = photometerUtils.cleanTess(_tess);

    var options = {
      new: true
    };
    if (isNew) {
      options['upsert'] = true;
    }

    Tess.findOneAndUpdate(
      query, {
        $set: _tess
      },
      options,
      function(errs, docs) {
        console.log(errs);
        if (docs) {
          delete docs["_id"];

          if (!req.body.noexec) {
            require('./helpers/utils').exec(PYTHON, [GRAFANA_PYTHON_SCRIPT, isNew ? 'add' : 'update', docs["name"], docs["mac"]], function(data) {});
          }

        }

        if (req.query.pretty) {
          res.json(JSON.stringify(docs, null, 4));
        } else {
          res.json(docs);
        }
      });
  };

  var token = req.body.token;
  if (!token) {

    if (!req.params.mac) {
      res.status(400);
      res.header('Tess_error', 'error_invalid_mac');
      res.send('error_invalid_mac');
      return;
    }

    delete tess_info["name"];
    delete tess_info["mac"];
    delete tess_info["info_tess"];
    _update(tess_info);
  } else {

    var grafanaUtils = require('./helpers/grafana_utils');
    grafanaUtils.isAdminRolAsync(token, function(result) {
      if ("success" in result) {
        isNew = req.body.isNew === true;
        _update(tess_info);
      } else {
        res.status(401);
        res.send({
          error: "Error"
        });
      }
    });
  }
});

/**
 * Check if user has access to Grafana panel
 * @param  {[type]} req [description]
 * @param  {[type]} res [description]
 * @return {json}     [description]
 */
router.post('/grafanaRole', function(req, res) {
  var grafanaUtils = require('./helpers/grafana_utils');

  grafanaUtils.isAdminRolAsync(req.body.token, function(result) {
    if ("error" in result) {
      res.status(401);
      res.send({
        error: result["error"]
      });
    } else if ("success" in result) {
      res.send({
        success: true
      });
    } else {
      res.status(401);
      res.send({
        error: "Error"
      });
    }
  });
});

router.post('/photometers_list', function(req, res) {
  var grafanaUtils = require('./helpers/grafana_utils');

  grafanaUtils.isAdminRolAsync(req.body.token, function(result) {
    if ("error" in result) {
      res.status(401);
      res.send({
        error: result["error"]
      });
    } else if ("success" in result) {
      Tess.find({}, {
        '_id': 0,
        'name': 1,
        'mac': 1,
        'info_location': 1
      }, function(errs, docs) {

        if (docs) {
          docs.sort(function(a, b) {
            var _a = parseInt(a.name);
            var _b = parseInt(b.name);
            return _a > _b;
          });
        }

        res.json(docs);
      });
    } else {
      res.status(401);
      res.send({
        error: "Error"
      });
    }
  });
});

router.post('/photometers_all', function(req, res) {
  var grafanaUtils = require('./helpers/grafana_utils');
  grafanaUtils.isAdminRolAsync(req.body.token, function(result) {
    if ("error" in result) {
      res.status(401);
      res.send({
        error: result["error"]
      });
    } else if ("success" in result) {
      Tess.find({}, {
        '_id': 0
      }, function(errs, docs) {
        res.json(docs);
      });
    } else {
      res.status(401);
      res.send({
        error: "Error"
      });
    }
  });
});

router.post('/photometers_new', function(req, res) {
  var grafanaUtils = require('./helpers/grafana_utils');
  grafanaUtils.isAdminRolAsync(req.body.token, function(result) {
    if ("error" in result) {
      res.status(401);
      res.send({
        error: result["error"]
      });
    } else if ("success" in result) {
      var d = new Date();
      d.setDate(d.getDate() - 1);
      Tess.distinct('name', {}, function(errs, distinct) {
        Last.distinct('name', {
          'name': {
            '$nin': distinct
          },
          'tstamp': {
            '$gt': d.toISOString()
          }
        }, function(errs, docs) {
          res.json(docs);
        });
      });
    } else {
      res.status(401);
      res.send({
        error: "Error"
      });
    }
  });
});

router.post('/grafana/sync', function(req, res) {
  var grafanaUtils = require('./helpers/grafana_utils');

  grafanaUtils.isAdminRolAsync(req.body.token, function(result) {
    if ("error" in result) {
      res.status(401);
      res.send({
        error: result["error"]
      });
    } else if ("success" in result) {
      res.end("ok");
      require('./helpers/utils').exec(PYTHON, [GRAFANA_PYTHON_SCRIPT, 'sync'], function(data) {
        //res.end(data);
      });

    } else {
      res.status(401);
      res.send({
        error: "Error"
      });
    }
  });
});


router.get('/photometers_fix', function(req, res) {
  Tess.find({
    mac: /-/
  }, function(errs, docs) {
    if (docs) {
      var photometerUtils = require('./helpers/photometer_utils');
      docs.forEach(function(doc) {
        var mac = photometerUtils.parseMAC(doc['mac']);
        if (mac) {
          Tess.findOneAndUpdate({
            name: doc['name'],
            mac: doc['mac'],
          }, {
            $set: {
              mac: mac
            }
          }, function(err, d) {});
        }
        console.log(doc['mac'] + " -> " + mac);
      });
    }
    res.send('ok');
  });
});

router.get('/photometers_emitting', function(req, res) {

  var moment = require('moment');
  var re = new RegExp('[0-9]+(y|M|w|d|h|ms|m|s)');

  var query_moment = moment().subtract(24, 'h');

  if (req.query.subtract && re.exec(req.query.subtract)) {
    var n = parseInt(re.exec(req.query.subtract)[0]);
    var unit = re.exec(req.query.subtract)[1];
    query_moment = moment().subtract(n, unit);
  }

  Last.distinct('name', {
    'tstamp': {
      '$gt': query_moment.toDate().toISOString()
    }
  }, function(errs, docs) {
    res.json(docs);
  });
});


router.get('/robots.txt', function(req, res) {
  res.type('text/plain');
  res.send("User-agent: Twitterbot\nDisallow: \n\nUser-agent: *\nDisallow: /");
});

router.get('/cardView/:name', function(req, res) {
  Tess.findOne({
    name: req.params.name
  }, function(errs, doc) {
    var meta = '';
    var ip = req.headers['x-forwarded-for'] || req.connection.remoteAddress;
    // console.log(ip)
    var rederic_url = GRAFANA_PROTOCOL + '://' + GRAFANA_HOST;

    meta += '<meta property="og:url" content="https://api.stars4all.eu/cardView/' + req.params.name + '">'

    meta += '<meta property="og:url" content="' + GRAFANA_PROTOCOL + '://' + GRAFANA_HOST + '">'
    meta += '<meta name="twitter:url" content="' + GRAFANA_PROTOCOL + '://' + GRAFANA_HOST + '">'

    meta += '<meta property="og:title" content="STARS4ALL - TESS-W">'
    meta += '<meta name="twitter:title" content="STARS4ALL - TESS-W">'

    meta += '<meta property="og:description" content="Designed by astronomers, compact, inexpensive">'
    meta += '<meta name="twitter:description" content="Designed by astronomers, compact, inexpensive">'

    meta += '<meta property="og:type" content="article">'

    meta += '<meta name="twitter:card" content="summary_large_image">'
    meta += '<meta name="twitter:site" content="@stars4all_eu">'

    if (doc) {

      rederic_url = GRAFANA_PROTOCOL + '://' + GRAFANA_HOST + '/d/datasheet_' + doc.name + '/' + doc.name;

      meta += '<meta property="og:url" content="' + GRAFANA_PROTOCOL + '://' + GRAFANA_HOST + '/d/datasheet_' + doc.name + '/' + doc.name + '">'
      meta += '<meta name="twitter:url" content="' + GRAFANA_PROTOCOL + '://' + GRAFANA_HOST + '/d/datasheet_' + doc.name + '/' + doc.name + '">'

      if (doc._full_location) {
        meta += '<meta property="og:description" content="' + doc._full_location + '">'
        meta += '<meta name="twitter:description" content="' + doc._full_location + '">'
      }

      meta += '<meta property="og:title" content="STARS4ALL - TESS-W ' + doc.name + '">'
      meta += '<meta name="twitter:title" content="STARS4ALL - TESS-W ' + doc.name + '">'

      var d = new Date();
      var n = d.getMilliseconds();

      meta += '<meta property="og:image" content="' + GRAFANA_PROTOCOL + '://' + GRAFANA_HOST + '/render/d-solo/datasheet_' + doc.name + '/' + doc.name + '?orgId=1&panelId=13&from=now&to=now-24h&width=1000&height=500&' + n + '">'
      meta += '<meta name="twitter:image" content="' + GRAFANA_PROTOCOL + '://' + GRAFANA_HOST + '/render/d-solo/datasheet_' + doc.name + '/' + doc.name + '?orgId=1&panelId=13&from=now&to=now-24h&width=1000&height=500&' + n + '">'
      meta += '<meta name="og:image:alt" content="Last measures">'

      meta += '<meta name="og:site_name" content="' + doc.name + '">'

    }

    var html = '<html><head>' + (meta ? meta : '') + '</head><body></body></html>';

    var whois = require('whois')
    whois.lookup(ip, function(err, data) {
      if (err) {
        res.redirect(rederic_url);
        return;
      }

      if (data.indexOf('Twitter') !== -1) {
        // console.log("From Twitter")
        // console.log(html)
        res.send(html);
        return;
      }
      if (data.indexOf('Facebook') !== -1) {
        // console.log("From Facebook")
        // console.log(html)
        res.send(html);
        return;
      }
      // console.log(data)

      res.redirect(rederic_url);
    })


  });
});
//******************************************************************************

router.get('/photometer/:id_tess/observations/:id_obs', function(req, res) {
  var id_tess = req.params.id_tess;

  var query;

  //Read fields
  var fields = req.query.fields;
  if (fields != null) {
    fields = fields.replace(/,/g, " ");
  } else {
    fields = '';
  }

  var maxCount = 100;
  var cursor = (req.query.cursor) ? parseInt(req.query.cursor) : 0;
  var count = (req.query.count) ? parseInt(req.query.count) : maxCount;
  var aux = (cursor - count);
  var before = (aux < 0) ? 0 : aux;
  var after = parseInt(cursor) + parseInt(count);

  var tstamp_sort = req.query.sort;
  var accuracy = req.query.accuracy;

  var beginInterval = req.query.begin;
  var endInterval = req.query.end;

  if ((beginInterval != null) && (endInterval != null)) {
    if (accuracy != null) {
      accuracy = Math.trunc(120 / accuracy);
      query = {
        name: id_tess,
        tstamp: {
          $gt: beginInterval,
          $lt: endInterval
        },
        $where: "this.seq % " + accuracy + " == 0"
      };
    } else {
      query = {
        name: id_tess,
        tstamp: {
          $gt: beginInterval,
          $lt: endInterval
        }
      };
    }
  } else if ((beginInterval != null) && (endInterval == null)) {
    query = {
      name: id_tess,
      tstamp: {
        $gt: beginInterval
      }
    };
  } else {
    query = {
      name: id_tess
    };
  }

  console.log("Query observation: %j", query);

  if (req.params.id_obs == "latest_values") {
    console.log("Send query " + new Date().getTime());
    Last.find(query, fields, {
      skip: cursor,
      limit: count,
      sort: {
        tstamp: 1
      }
    }, function(errs, docs) {
      if (errs) {
        res.json(500);
      } else {
        console.log("Last values " + new Date().getTime());
        res.json(docs);
      }
    });
  } else {
    Observations.findOne({
      _id: req.params.id_obs
    }, fields, function(errs, doc) {
      res.json(doc);
    });
  }

});

router.get('/photometer/:id_tess/observations', function(req, res) {
  var id_tess = req.params.id_tess;

  //	var link = req.protocol+"://"+req.hostname+":"+PORT+"/api/v1/photometers/"+id_tess+"/observations/";

  var query;

  //Read fields
  var fields = req.query.fields;
  if (fields != null) {
    fields = fields.replace(/,/g, " ");
    fields = fields + ' _id';
  } else {
    fields = '_id';
  }
  //Pagination variables
  var maxCount = 100;
  var cursor = (req.query.cursor) ? parseInt(req.query.cursor) : 0;
  var count = (req.query.count) ? parseInt(req.query.count) : maxCount;
  var aux = (cursor - count);
  var before = (aux < 0) ? 0 : aux;
  var after = parseInt(cursor) + parseInt(count);
  var link = "https://api.stars4all.eu/photometer/" + id_tess + "/observations";


  var beginInterval = req.query.begin;
  var endInterval = req.query.end;

  var tstamp_sort = req.query.sort;
  var accuracy = req.query.accuracy;

  if (tstamp_sort == null) {
    tstamp_sort = 1;
  }

  if ((beginInterval != null) && (endInterval != null)) {
    if (accuracy != null) {
      accuracy = Math.trunc(120 / accuracy);
      query = {
        name: id_tess,
        tstamp: {
          $gt: beginInterval,
          $lt: endInterval
        },
        $where: "this.seq % " + accuracy + " == 0"
      };
    } else {
      query = {
        name: id_tess,
        tstamp: {
          $gt: beginInterval,
          $lt: endInterval
        }
      };
    }
  } else if ((beginInterval != null) && (endInterval == null)) {
    query = {
      name: id_tess,
      tstamp: {
        $gt: beginInterval
      }
    };
  } else {
    query = {
      name: id_tess
    };
  }

  console.log("Query observations: %j", query);

  Last.find(query, fields, {
    skip: cursor,
    limit: count,
    sort: {
      tstamp: -1
    }
  }, function(errs, docs) {
    if (errs) {
      res.json(500);
    } else {

      Observations.count({
        name: id_tess
      }, function(err, c) {

        res.append('X-Total-Count', c);

        var link_previous = link + "?cursor=" + before + "&count=" + count;
        var link_next = link + "?cursor=" + after + "&count=" + count;
        var data_result = JSON.parse(JSON.stringify(docs));

        for (var i in docs) {
          data_result[i]["links"] = {
            self: link + "/" + data_result[i]["_id"]
          };
          delete data_result[i]["_id"];
        }
        res.links({
          next: link_next,
          prev: link_previous
        });

        res.json(data_result);
      });

    }
  });

});

router.post('/reports/new', function(req, res) {
  var photometers = req.body.photometers;
  var sensors = req.body.sensors

  var report = Report(req.body);
  console.log("Report:" + report);
  console.log(photometers + " " + sensors);

  Report.findOne({
    $and: [{
      photometers: photometers
    }, {
      sensors: sensors
    }]
  }, function(errs, docs) {
    if (errs) {
      res.json(500);
    } else {
      var link = req.protocol + "://" + req.hostname + "/api/reports/";
      if (docs == null) {
        console.log("Inserting new report");
        report.save(function(err) {
          if (err) {
            res.json(500);
          }
          var newLink = link + report._id;
          res.status(200).json({
            href: newLink
          });
        });
      } else {
        console.log("Existing report");
        link = link + docs._id;
        res.status(200).json({
          href: link
        });
      }
    }
  });



});

router.get('/reports', function(req, res) {
  Report.find({}, function(errs, docs) {
    if (errs) {
      res.json(500);
    } else {
      res.status(200).json(docs);
    }
  });
});

router.get('/reports/instant_values', function(req, res) {

  var maxCount = 100;
  var count = (req.query.count) ? parseInt(req.query.count) : maxCount;


  var fields = req.query.fields;
  if (fields != null) {
    fields = fields.replace(/,/g, " ");
    fields = fields + ' _id';
  } else {
    fields = 'name mag tstamp';
  }

  Last.find({}, fields, {
    limit: count,
    sort: {
      tstamp: -1
    }
  }, function(obs_error, obs_docs) {
    if (obs_error) {
      res.json(500);
    } else {
      res.json(obs_docs);
    }
  });

});

app.use(router)

app.listen(PORT);

console.log("Running on server:" + PORT);
