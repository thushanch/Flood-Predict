// Sri Lanka river sediment explorer -- paste into code.earthengine.google.com
// Visual QA: station placement, water mask, seasonal SPM / turbidity maps,
// and a click-anywhere time series. Same coefficients as sedrs/algorithms.py.

var YEAR = 2024;
var SEASON = 'SWM';                 // NEM (Dec-Feb), FIM (Mar-Apr), SWM (May-Sep), SIM (Oct-Nov)
var CS_THRESHOLD = 0.60;            // Cloud Score+ cs_cdf
var JRC_MIN = 50, ERODE_M = 30, SWIR_MAX = 0.04;   // Sen2Cor BOA limit, see sedrs/algorithms.py

// Approximate station coordinates (replace with config/stations_snapped.yaml values)
var stations = ee.FeatureCollection([
  ['kelani_kitulgala', 80.4172, 6.9893], ['kelani_hanwella', 80.0820, 6.9105],
  ['kelani_colombo', 79.8800, 6.9600], ['kalu_ratnapura', 80.3990, 6.6850],
  ['kalu_ellagawa', 80.2150, 6.7300], ['kalu_putupaula', 80.0500, 6.6100],
  ['gin_baddegama', 80.1800, 6.1700], ['gin_gintota', 80.1650, 6.0700],
  ['nilwala_matara', 80.5380, 5.9550], ['mahaweli_peradeniya', 80.5950, 7.2650],
  ['mahaweli_mahiyangana', 80.9900, 7.3230], ['mahaweli_manampitiya', 81.0900, 7.9150],
  ['mahaweli_somawathiya', 81.1700, 8.1300], ['walawe_embilipitiya', 80.8500, 6.3300],
  ['walawe_ambalantota', 81.0250, 6.1200], ['deduru_chilaw', 79.8350, 7.6080],
  ['mahaoya_badalgama', 79.9800, 7.2900]
].map(function (s) { return ee.Feature(ee.Geometry.Point([s[1], s[2]]), {id: s[0]}); }));

var sriLanka = ee.Geometry.Rectangle([79.5, 5.85, 81.95, 9.9]);

var water = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('occurrence')
  .gte(JRC_MIN).unmask(0).focalMin({radius: ERODE_M, units: 'meters'});

function nechad(rho, A, C) { return rho.multiply(A).divide(ee.Image(1).subtract(rho.divide(C))); }
function valid(rho, C) { return rho.gt(0).and(rho.lt(C)); }
function blend(redEst, nirEst, redOk, nirOk, rhoRed) {
  var w = rhoRed.subtract(0.05).divide(0.02).clamp(0, 1);
  var out = redEst.multiply(ee.Image(1).subtract(w)).add(nirEst.multiply(w))
    .where(w.lte(0), redEst).where(w.gte(1), nirEst);
  return out.updateMask(w.gte(1).or(redOk).and(w.lte(0).or(nirOk)));
}

function s2Products(img) {
  var clear = img.select('cs_cdf').gte(CS_THRESHOLD);
  var r = img.select(['B3', 'B4', 'B8A', 'B11'], ['green', 'red', 'nir', 'swir1'])
    .divide(10000).updateMask(clear);
  var g = r.select('green'), red = r.select('red'), nir = r.select('nir'), s = r.select('swir1');
  var mask = water.and(s.lt(SWIR_MAX)).and(g.subtract(s).divide(g.add(s)).gt(0))
    .and(red.gt(0)).and(g.gt(0));
  var ndti = red.subtract(g).divide(red.add(g)).rename('ndti');
  var tdog = blend(nechad(red, 228.1, 0.1641), nechad(nir, 3078.9, 0.2112),
                   valid(red, 0.1641), valid(nir, 0.2112), red).rename('T_dog');
  var spm = blend(nechad(red, 342.10, 0.19563), nechad(nir, 2932.21, 0.21151),
                  valid(red, 0.19563), valid(nir, 0.21151), red).rename('SPM_blend');
  return ee.Image(ee.Image.cat([ndti, tdog, spm]).updateMask(mask)
    .copyProperties(img, ['system:time_start']));
}

function s2(start, end, region) {
  return ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(region).filterDate(start, end)
    .linkCollection(ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED'), ['cs_cdf'])
    .map(s2Products);
}

var ranges = {
  NEM: [(YEAR - 1) + '-12-01', YEAR + '-03-01'], FIM: [YEAR + '-03-01', YEAR + '-05-01'],
  SWM: [YEAR + '-05-01', YEAR + '-10-01'], SIM: [YEAR + '-10-01', YEAR + '-12-01']
};
var col = s2(ranges[SEASON][0], ranges[SEASON][1], sriLanka);
var comp = col.median();

var pal = ['#08306b', '#2171b5', '#6baed6', '#fdd49e', '#fc8d59', '#b30000'];
Map.setCenter(80.7, 7.6, 8);
Map.addLayer(water.selfMask(), {palette: ['00ffff']}, 'Stable water (eroded)', false);
Map.addLayer(comp.select('SPM_blend'), {min: 1, max: 150, palette: pal}, 'SPM ' + SEASON + ' ' + YEAR);
Map.addLayer(comp.select('T_dog'), {min: 1, max: 150, palette: pal}, 'Turbidity FNU', false);
Map.addLayer(comp.select('ndti'), {min: -0.3, max: 0.3, palette: pal}, 'NDTI', false);
Map.addLayer(col.select('SPM_blend').count(), {min: 0, max: 20, palette: ['red', 'yellow', 'green']},
             'Clear observations', false);
Map.addLayer(stations, {color: 'yellow'}, 'Stations (approx)');
Map.addLayer(stations.map(function (f) { return f.buffer(500); }).style({color: 'yellow', fillColor: '00000000'}),
             {}, 'Station AOIs (500 m)');

// Click -> 500 m SPM time series, full record
var panel = ui.Panel({style: {width: '420px'}});
ui.root.add(panel);
panel.add(ui.Label('Click on a river to plot SPM (median of water pixels within 500 m)'));
Map.onClick(function (c) {
  var aoi = ee.Geometry.Point([c.lon, c.lat]).buffer(500);
  var ts = s2('2019-01-01', '2026-10-01', aoi).select('SPM_blend');
  panel.widgets().set(1, ui.Chart.image.series(ts, aoi, ee.Reducer.median(), 20)
    .setOptions({title: 'SPM_blend (g m-3)', pointSize: 3, lineWidth: 0, vAxis: {scaleType: 'log'}}));
});
