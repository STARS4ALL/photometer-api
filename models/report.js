var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var ReportSchema = new Schema({
	photometers: [String],
        sensors: [String]

});

var Report = mongoose.model('Report', ReportSchema,'reports');

module.exports.Report = Report;
module.exports.Schema = ReportSchema;
