var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var TessSchema = new Schema({
        name:String,
	mac:String,
        location:String,
        tester:String,
	latitude:Number,
	longitude:Number
});

var Tess = mongoose.model('Photometer', TessSchema,'tess');

module.exports.Tess = Tess;
module.exports.Schema = TessSchema;
