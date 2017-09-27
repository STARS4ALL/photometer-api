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
var Crowd = require('./models/crowdstats.js').CrowdStats;

const PORT = 8888;

//DB Models


mongoose.connect(DATABASE_HOST+DATABASE_NAME, function(err,res) {

	if(err){
		console.log('ERROR: connecting with db ' + err + ' '+res);
	}
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

router.get('/', function (req, res){
	res.json({ message: 'Hello world\n' });
});

router.get('/info', function (req, res){
	res.json({project:'STARS4ALL', description: 'This is a REST API to access to the photometers data', funded:' By European Union ( H2020 framework -> 688135)'});
});

router.get('/crowdsourcing', function (req, res){

	var beginInterval = req.query.begin;
	var endInterval = req.query.end;
	var project = req.query.project;

	var query;

	if ((beginInterval!=null) && (endInterval!=null)){
		query = {date: {$gt: beginInterval, $lt: endInterval}};
	} else if ((beginInterval!=null) && (endInterval==null)){
		query = {date: {$gt : beginInterval}};
	} else{
		query = {};
	}

	if (project!=null){
		query["project"]=project;
	}

	Crowd.find(query, function (errs,docs){
		res.json(docs);
	});
});

router.get('/photometers', function (req, res){

	Tess.find({}, function (errs,docs){
		res.json(docs);
	});
});

router.get('/photometers/:id', function (req, res){

	Tess.findOne({name:req.params.id}, function (errs, docs){
	
		if (req.query.pretty){
			res.json(JSON.stringify(docs, null, 4));
		} else {	
			res.json(docs);
		}
	});

});

router.get('/photometers/:id_tess/observations/:id_obs', function(req, res){

	
	var id_tess = req.params.id_tess;

	var query;

	//Read fields
	var fields = req.query.fields;
	if (fields!=null){
		fields = fields.replace(/,/g," ");
	} else {
		fields = '';
	}

	var maxCount = 100;
	var cursor = (req.query.cursor) ? req.query.cursor : 0;
	var count = (req.query.count) ? req.query.count : maxCount;
	var aux = (cursor - count);
	var before = (aux < 0) ? 0 : aux;
	var after = parseInt(cursor)+parseInt(count);

	var tstamp_sort = req.query.sort;
	var accuracy = req.query.accuracy;

	var beginInterval = req.query.begin;
        var endInterval = req.query.end;

	if ((beginInterval != null) && (endInterval!=null)){
                if (accuracy!= null){
                        accuracy = Math.trunc(120 / accuracy);
                        query = {name:id_tess, tstamp: {$gt : beginInterval, $lt: endInterval}, $where:"this.seq % "+accuracy+" == 0"};
                }else {
                        query = {name:id_tess, tstamp: {$gt : beginInterval, $lt: endInterval}};
                }
        } else if ((beginInterval != null) && (endInterval == null)){
                query = {name:id_tess, tstamp : {$gt: beginInterval}};
        } else {
                query = {name:id_tess};
        }

	console.log("Query observation: %j", query);

	if (req.params.id_obs=="latest_values"){
		console.log("Send query "+new Date().getTime());
		Last.find(query, fields, {skip: cursor, limit:count, sort:{tstamp:1}} , function (errs, docs){
			if (errs){
                        	res.json(500);
                	} else {
				console.log("Last values "+new Date().getTime());
				res.json(docs);
			}	
		});
	} else {
		Observations.findOne({ _id: req.params.id_obs}, fields,  function (errs, doc){
			res.json(doc);
		});
	}
	
});

router.get('/photometers/:id_tess/observations', function(req, res){

	var id_tess = req.params.id_tess;

//	var link = req.protocol+"://"+req.hostname+":"+PORT+"/api/v1/photometers/"+id_tess+"/observations/"; 

	var query;

	//Read fields
	var fields = req.query.fields;
	if (fields!=null){
		fields = fields.replace(/,/g," ");
		fields = fields + ' _id';
	} else {
		fields = '_id';
	}
	//Pagination variables
	var maxCount = 100;
	var cursor = (req.query.cursor) ? req.query.cursor : 0; 
	var count = (req.query.count) ? req.query.count : maxCount;
	var aux = (cursor-count);
	var before = ( aux < 0) ? 0 : aux;
	var after =parseInt(cursor)+parseInt(count);
	var link = "http://api.stars4all.eu/photometers/"+id_tess+"/observations/";


	var beginInterval = req.query.begin;
	var endInterval = req.query.end;

	var tstamp_sort = req.query.sort;
	var accuracy = req.query.accuracy;

	if (tstamp_sort == null){
		tstamp_sort = 1;
	}

	if ((beginInterval != null) && (endInterval!=null)){
		if (accuracy!= null){
			accuracy = Math.trunc(120 / accuracy);
			query = {name:id_tess, tstamp: {$gt : beginInterval, $lt: endInterval}, $where:"this.seq % "+accuracy+" == 0"};		
		}else {
			query = {name:id_tess, tstamp: {$gt : beginInterval, $lt: endInterval}};
		}
	} else if ((beginInterval != null) && (endInterval == null)){
		query = {name:id_tess, tstamp : {$gt: beginInterval}};
	} else {
		query = {name:id_tess};
	}


	console.log("Query observations: %j", query);
	Observations.find(query, fields ,{skip: cursor, limit:count, sort:{tstamp:-1}} , function (errs, docs){
	
		if (errs){
			res.json(500);
		} else {

		

			Observations.count({name:id_tess}, function(err, c){
				
				res.append('X-Total-Count',c);

				var link_previous = link+"?cursor="+before+"&count="+count;
				var link_next = link+"?cursor="+after+"&count="+count;
				var data_result = JSON.parse(JSON.stringify(docs));
		
				for (var i in docs){
					data_result[i]["links"]={self: link+data_result[i]["_id"]};
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

router.post('/reports/new', function(req, res){
	var photometers = req.body.photometers;
	var sensors = req.body.sensors

	var report = Report(req.body);
	console.log("Report:"+report);
	console.log(photometers+" "+sensors);

	Report.findOne({ $and: [{photometers:photometers},{sensors:sensors}] }, function(errs, docs){
		if (errs){
			res.json(500);
		} else {
			var link = req.protocol+"://"+req.hostname+"/api/reports/";
			if (docs == null){
				console.log("Inserting new report");
				report.save(function (err){
					if (err) {
						res.json(500);
					}
					var newLink = link + report._id;
					res.status(200).json({href:newLink});
	}			);
			} else {
				console.log("Existing report"); 
				link = link+docs._id;
				res.status(200).json({href:link});
			}
		}
	});



});

router.get('/reports', function(req, res){
	Report.find({}, function (errs,docs){
		if (errs){
			res.json(500);
		}else {
			res.status(200).json(docs);
		}
	});
});

router.get('/reports/instant_values', function(req, res){

	var maxCount = 100;
	var count = (req.query.count) ? req.query.count : maxCount;


	var fields = req.query.fields;
        if (fields!=null){
                fields = fields.replace(/,/g," ");
                fields = fields + ' _id';
        } else {
                fields = 'name mag tstamp';
        }

	Last.find({}, fields, {limit:count, sort:{tstamp:-1}}, function (obs_error, obs_docs){
		if (obs_error){
			res.json(500);
		} else {
			res.json(obs_docs);	
		}
	});

});

app.use(router)

app.listen(PORT);

console.log("Running on server:"+PORT); 
