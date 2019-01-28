/* Module for handling the spatial querying
 */
this.ckan.module('odsh-spatial-query', function ($, _)
{

  return {
    options: {
      i18n: {
      },
      style: {
        color: '#F06F64',
        weight: 2,
        opacity: 1,
        fillColor: '#F06F64',
        fillOpacity: 0.1,
        clickable: false
      },
      default_extent: [[90, 180], [-90, -180]]
    },
    template: {
      buttons: [
        '<div id="dataset-map-edit-buttons-text">',
        'Wählen Sie mit dem rechten Quadrat Ihren gesuchten Bereich aus und bestätigen Sie mit &quot;Anwenden&quot;',
        '</div>',
        '<div id="dataset-map-edit-buttons">',
        '<a href="javascript:;" class="btn btn-arrow-right cancel">Abbrechen</a> ',
        '<a href="javascript:;" class="btn btn-primary btn-arrow-right apply disabled">Anwenden</a>',
        '</div>'
      ].join('')
    },

    initialize: function ()
    {
      var module = this;
      $.proxyAll(this, /_on/);

      var user_default_extent = this.el.data('default_extent');
      if (user_default_extent)
      {
        if (user_default_extent instanceof Array)
        {
          // Assume it's a pair of coords like [[90, 180], [-90, -180]]
          this.options.default_extent = user_default_extent;
        } else if (user_default_extent instanceof Object)
        {
          // Assume it's a GeoJSON bbox
          this.options.default_extent = new L.GeoJSON(user_default_extent).getBounds();
        }
      }
      this.el.ready(this._onReady);
    },

    _getParameterByName: function (name)
    {
      var match = RegExp('[?&]' + name + '=([^&]*)')
        .exec(window.location.search);
      return match ?
        decodeURIComponent(match[1].replace(/\+/g, ' '))
        : null;
    },

    _drawExtentFromCoords: function (xmin, ymin, xmax, ymax)
    {
      if ($.isArray(xmin))
      {
        var coords = xmin;
        xmin = coords[0]; ymin = coords[1]; xmax = coords[2]; ymax = coords[3];
      }
      return new L.Rectangle([[ymin, xmin], [ymax, xmax]],
        this.options.style);
    },

    _drawExtentFromGeoJSON: function (geom)
    {
      return new L.GeoJSON(geom, { style: this.options.style });
    },

    _onReady: function ()
    {
      var module = this;
      var map;
      var extentLayer;
      var previous_box;
      var previous_extent;
      var is_exanded = false;
      var should_zoom = true;
      var form = $("#dataset-search");
      // CKAN 2.1
      if (!form.length)
      {
        form = $(".search-form");
      }

      var buttons;

      // Add necessary fields to the search form if not already created
      $(['ext_bbox', 'ext_prev_extent']).each(function (index, item)
      {
        if ($("#" + item).length === 0)
        {
          $('<input type="hidden" />').attr({ 'id': item, 'name': item }).appendTo(form);
        }
      });

      // OK map time
      // var crs = L.CRS.project('EPSG:25832', '+proj=utm +zone=32 +ellps=GRS80 +units=m +no_defs', new L.Transformation(0.5 / (Math.PI * L.Projection.Mercator.R_MAJOR), 0.5, -0.5 / (Math.PI * L.Projection.Mercator.R_MINOR), 0.5));
      //  var crs = L.Proj.CRS('EPSG:25832', '+proj=utm +zone=32 +ellps=GRS80 +units=m +no_defs', new L.Transformation(0.5 / (Math.PI * L.Projection.Mercator.R_MAJOR), 0.5, -0.5 / (Math.PI * L.Projection.Mercator.R_MINOR), 0.5));
      // var crs = new L.Proj.CRS('EPSG:25832',
      //   '+proj=utm +zone=32 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs',
      //   {
      //     resolutions: [2000, 1100, 550, 275, 100, 50, 25, 10, 5, 2, 1, 0.5, 0.25]//,
      //     //origin: [0, 0]
      //   }),
      map = ckan.commonLeafletMap(
        'dataset-map-container',
        this.options.map_config,
        {
          attributionControl: false,
          drawControlTooltips: false,
          // crs: crs
          zoomControl: false
        }
      );

//       var wmsLayer = L.tileLayer.wms('https://demo.boundlessgeo.com/geoserver/ows?', {
//     layers: 'ne:ne'
// }).addTo(map);

      L.control.zoom({
        zoomInTitle: 'Vergrößern',
        zoomOutTitle: 'Verkleinern',
      }).addTo(map);

      const drawControl = new L.Control.Draw({
        position: 'topright',
        draw: {
          polyline: false,
          polygon: false,
          circle: false,
          marker: false,
          rectangle: { shapeOptions: module.options.style }
        }
      });
      L.drawLocal.draw.toolbar.buttons.rectangle = 'Rechteck ziehen'
      // Initialize the draw control
      map.addControl(drawControl);

      // OK add the expander
      $('a.leaflet-draw-draw-rectangle', module.el).on('click', function (e)
      {
        if (!is_exanded)
        {
          $('body').addClass('dataset-map-expanded');
          if (should_zoom && !extentLayer)
          {
            map.zoomIn();
          }
          resetMap();
          is_exanded = true;
        }
      });

      // Setup the expanded buttons
      buttons = $(module.template.buttons).insertBefore('#dataset-map-attribution');

      // Handle the cancel expanded action
      $('.cancel', buttons).on('click', function ()
      {
        $('body').removeClass('dataset-map-expanded');
        if (extentLayer)
        {
          map.removeLayer(extentLayer);
        }
        setPreviousExtent();
        setPreviousBBBox();
        resetMap();
        is_exanded = false;
      });

      // Handle the apply expanded action
      $('.apply', buttons).on('click', function ()
      {
        if (extentLayer)
        {
          $('body').removeClass('dataset-map-expanded');
          is_exanded = false;
          resetMap();
          // Eugh, hacky hack.
          setTimeout(function ()
          {
            map.fitBounds(extentLayer.getBounds());
            submitForm();
          }, 200);
        }
      });

      // When user finishes drawing the box, record it and add it to the map
      map.on('draw:created', function (e)
      {
        if (extentLayer)
        {
          map.removeLayer(extentLayer);
        }
        extentLayer = e.layer;
        $('#ext_bbox').val(extentLayer.getBounds().toBBoxString());
        map.addLayer(extentLayer);
        $('.apply', buttons).removeClass('disabled').addClass('btn-primary');
      });

      // Record the current map view so we can replicate it after submitting
      map.on('moveend', function (e)
      {
        $('#ext_prev_extent').val(map.getBounds().toBBoxString());
      });

      // Ok setup the default state for the map
      var previous_bbox;
      setPreviousBBBox();
      setPreviousExtent();

      // OK, when we expand we shouldn't zoom then
      map.on('zoomstart', function (e)
      {
        should_zoom = false;
      });


      // Is there an existing box from a previous search?
      function setPreviousBBBox()
      {
        previous_bbox = module._getParameterByName('ext_bbox');
        if (previous_bbox)
        {
          $('#ext_bbox').val(previous_bbox);
          extentLayer = module._drawExtentFromCoords(previous_bbox.split(','))
          map.addLayer(extentLayer);
          map.fitBounds(extentLayer.getBounds());
        }
      }

      // Is there an existing extent from a previous search?
      function setPreviousExtent()
      {
        previous_extent = module._getParameterByName('ext_prev_extent');
        if (previous_extent)
        {
          coords = previous_extent.split(',');
          map.fitBounds([[coords[1], coords[0]], [coords[3], coords[2]]]);
        } else
        {
          if (!previous_bbox)
          {
            map.fitBounds(module.options.default_extent);
          }
        }
      }

      // Reset map view
      function resetMap()
      {
        L.Util.requestAnimFrame(map.invalidateSize, map, !1, map._container);
      }

      // Add the loading class and submit the form
      function submitForm()
      {
        setTimeout(function ()
        {
          form.submit();
        }, 800);
      }
    }
  }
});
