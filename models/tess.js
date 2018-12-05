var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var TessOrgSchema = new Schema({
  name: String,
  logo_url: String,
  description: String,
  web_url: String,
  phone: String,
  mail: String
}, {
  _id: false
});

var TessLocationSchema = new Schema({
  place: String,
  town: String,
  sub_region: String,
  region: String,
  country: String,
  latitude: Number,
  longitude: Number,
  openstreetmap_node: String
}, {
  _id: false
});

var TessContactSchema = new Schema({
  name: String,
  phone: String,
  mail: String,
  telegram_chat_id: String
}, {
  _id: false
});

var TessImagesSchema = new Schema({
  urls: [String]
}, {
  _id: false
});

var TessValuesSchema = new Schema({
  zero_point: Number,
  filters: String,
  mov_sta_position: String,
  local_timezone: String,
  period: Number
}, {
  _id: false
});

var TessSchema = new Schema({
  name: String,
  mac: String,
  //    location: String,
  //    tester: String,
  //    latitude: Number,
  //    longitude: Number,
  //-----------------
  info_org: TessOrgSchema,
  info_location: TessLocationSchema,
  info_contact: TessContactSchema,
  info_img: TessImagesSchema,
  info_tess: TessValuesSchema
  //-----------------

});

TessSchema
  .virtual('_full_location')
  .get(function() {
    var full_location = [];
    if (!this.info_location)
      return undefined;

    if (this.info_location.place) full_location.push(this.info_location.place)
    if (this.info_location.town) full_location.push(this.info_location.town)
    if (this.info_location.sub_region) full_location.push(this.info_location.sub_region)
    if (this.info_location.region) full_location.push(this.info_location.region)
    if (this.info_location.country) full_location.push(this.info_location.country)

    if (full_location.length > 0) {
      return full_location.join(', ')
    } else {
      return undefined;
    }
  });


var Tess = mongoose.model('Photometer', TessSchema, 'tess');

module.exports.Tess = Tess;
module.exports.Schema = TessSchema;
