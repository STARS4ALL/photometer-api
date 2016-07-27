'use strict';

const express = require('express');
const mongoose = require('mongoose');
const bodyParser = require('body-parser');


//Import mongodb models
var Tess = require('./models/tess.js').Tess;
var Observations = require('./models/observation.js').Observations;
var Report = require('./models/report.js').Report;
var config = require('./config.js');

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

router.get('/api/v1/info', function (req, res){
	res.json({project:'STARS4ALL', description: 'This is a REST API to access to the photometers data', funded:' By European Union ( H2020 framework -> 688135)'});
});

router.get('/api/v1/photometers', function (req, res){

	Tess.find({}, function (errs,docs){
		res.json(docs);
	});
});

router.get('/api/v1/photometers/:id', function (req, res){

	Tess.findOne({name:req.params.id}, function (errs, docs){
	
		if (req.query.pretty){
			res.json(JSON.stringify(docs, null, 4));
		} else {	
			res.json(docs);
		}
	});

});

router.get('/api/v1/photometers/:id_tess/observations/:id_obs', function(req, res){

	

	//Read fields
	var fields = req.query.fields;
	if (fields!=null){
		fields = fields.replace(/,/g," ");
	} else {
		fields = '';
	}

	Observations.findOne({ _id: req.params.id_obs}, fields,  function (errs, doc){
		res.json(doc);
	});
	

});

router.get('/api/v1/photometers/:id_tess/observations', function(req, res){

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
	var link = "http://api.stars4all.eu/api/v1/photometers/"+id_tess+"/observations/";


/*	var time = req.query.tstamp;
	var q2;
	if (time!=null){
		query["tstamp"]=/time/;
		q2 = {name:id_tess, tstamp:/time/};
	}else{
		q2 = {name:id_tess};
	}
	console.log(query+" "+time);
*/	
	var beginInterval = req.query.begin;
	var endInterval = req.query.end;

	if ((beginInterval != null) && (endInterval!=null)){
		query = {name:id_tess, tstamp: {$gt : beginInterval, $lt: endInterval}};		
	} else if ((beginInterval != null) && (endInterval == null)){
		query = {name:id_tess, tstamp : {$gt: beginInterval}};
	} else {
		query = {name:id_tess};
	}
	console.log("Query: %j", query);
	Observations.find(query, fields ,{skip: cursor, limit:count} , function (errs, docs){
	
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

router.post('/api/v1/reports/new', function(req, res){
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

router.get('/api/v1/reports', function(req, res){
	Report.find({}, function (errs,docs){
		if (errs){
			res.json(500);
		}else {
			res.status(200).json(docs);
		}
	});
});

router.get('/api/v1/reports/:id', function(req, res){

	var maxCount = 100;
	//var limit = req.query.limit;
	//var previous_count = req.query.previuos_count;
	var cursor = (req.query.cursor) ? req.query.cursor : 0; 
	var count = (req.query.count) ? req.query.count : maxCount;
	var aux = (cursor-count);
	var before = ( aux < 0) ? 0 : aux;
	var after =parseInt(cursor)+parseInt(count);
	var link = req.protocol+"://"+req.hostname+":"+PORT+"/api/reports/"+req.params.id;

	//Looking for a report
	Report.findOne({_id:req.params.id}, function (errs, docs){
		if (errs){
			res.json(500);
		} else {
			console.log('Photometers list:'+docs);

			var fields = "' "+docs.sensors+" '";
			fields = fields.replace(",", " ");

			//Check count

			Observations.find(docs.photometers, fields, {skip: cursor, limit:count}, function (obs_errs, obs_docs){
				if (obs_errs){
					res.json(500);
				} else {
					var link_previous = link+"?cursor="+before+"&count="+count;
					var link_next = link+"?cursor="+after+"&count="+count;
					//var result = "{ data: "+JSON.stringify(obs_docs,null,' ')+"}"
					//var result2 = { data: obs_docs, paging: { cursors : { after : after, before : before}, previous: link_previous, next:link_next}}
					res.links({
						prev: link_previous,
						next: link_next
					});
					res.json(obs_docs);
				}
			});
		}
	});
});

app.use(router)

app.listen(PORT);

console.log("Running on server:"+PORT); 
