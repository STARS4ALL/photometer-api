var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var TessSchema = new Schema({
        id:String,
        location:String,
        owner:String
});

var Tess = mongoose.model('Photometer', TessSchema, 'photometers');

module.exports.Tess = Tess;
module.exports.Schema = TessSchema;
