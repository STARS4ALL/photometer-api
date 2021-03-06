var mongoose = require('mongoose');
var Schema = mongoose.Schema;

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
var last_observations = mongoose.model('last_observation', ObservationSchema,'last_observations');

module.exports.Observations = Observations;
module.exports.last_observations = last_observations;
module.exports.Schema = ObservationSchema;
