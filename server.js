'use strict';

const express = require('express');
const mongoose = require('mongoose');
const bodyParser = require('body-parser');
//const Tess = require('./models/Tess.js');


const PORT = 8888;

//DB Models


mongoose.connect('mongodb://photometerdb/photometers', function(err,res) {

	if(err){
		console.log('ERROR: connecting with db ' + err + ' '+res);
	}
});

var Schema = mongoose.Schema;
var TessSchema = new Schema({
        id:String,
        location:String,
        owner:String
});
var Tess = mongoose.model('Photometer', TessSchema, 'photometers');

var ObservationSchema = new Schema({
	name:String,
	seq:Number,
	tamb:Number,
	rev:Number,
	tsky:Number,
	mag:Number,
	freq:Number
});
var Observations = mongoose.model('Observation',ObservationSchema,'observations');

var ReportSchema = new Schema({
	photometers: [String],
	sensors: [String]
});
var Reports = mongoose.model('Report', ReportSchema,'reports');

//App

var app = express();

//app.use(bodyParser.urlencoded({ extended:true }));
app.use(bodyParser.json());


var router = express.Router();

router.get('/', function (req, res){
	res.json({ message: 'Hello world\n' });
});

router.get('/api/info', function (req, res){
	res.json({project:'STARS4ALL', description: 'This is a REST API to access to the photometers data', funded:' By European Union ( H2020 framework -> 688135)'});
});

router.get('/api/photometers', function (req, res){

	Tess.find({}, function (errs,docs){
		res.json(docs);
	});
});

router.get('/api/photometers/:id', function (req, res){

	Tess.findOne({name:req.params.id}, function (errs, docs){
	
		if (req.query.pretty){
			res.json(JSON.stringify(docs, null, 4));
		} else {	
			res.json(docs);
		}
	});

});

router.get('/api/observations/:id', function(req, res){

	var page = (req.query.page) ? req.query.page : 0; 
	var startItem = page*20;


	Observations.find({name:req.params.id}, 'name seq freq mag tamb tsky wdBm', {skip: startItem, limit:20}, function (errs, docs){
		res.json(docs);
	});
	

});

router.post('/api/reports/new', function(req, res){
	var photometers = req.body.photometers;
	var sensors = req.body.sensors

	var report = Reports(req.body);
	console.log("Report:"+report);
	console.log(photometers+" "+sensors);

	Reports.findOne({ $and: [{photometers:photometers},{sensors:sensors}] }, function(errs, docs){
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

router.get('/api/reports/:id', function(req, res){

	var maxCount = 100;
	//var limit = req.query.limit;
	//var previous_count = req.query.previuos_count;
	var cursor = (req.query.cursor) ? req.query.cursor : 0; 
	var count = (req.query.count) ? req.query.count : maxCount;
	var aux = (cursor-count);
	var before = ( aux < 0) ? 0 : aux;
	var after =parseInt(cursor)+parseInt(count);
	var link = req.protocol+"://"+req.hostname+"/api/reports/"+req.params.id;

	//Looking for a report
	Reports.findOne({_id:req.params.id}, function (errs, docs){
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
					var result = "{data:"+JSON.stringify(obs_docs,null,4)+", paging:{cursors:{after:"+after+",before:"+before+"},previous:"+link_previous+",next:"+link_next+"}}";
					res.json(result);
				}
			});
		}
	});
});

app.use(router)

app.listen(PORT);

console.log("Running on server:"+PORT); 

