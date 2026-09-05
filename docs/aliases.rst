=============================
Compatibility alias reference
=============================

UltraPlot's official documentation and function signatures exclusively use
canonical parameter names. Alternative shorthand spellings (aliases) remain fully
supported through silent, behind-the-scenes keyword translation.

* **Context-dependent:** A single shorthand alias might map to different underlying
  Matplotlib properties depending on the artist type.
* **Silent translation:** Using aliases will not trigger deprecation warnings in
  the current version, though these may be enabled in a future release.
* **RC settings:** Entries marked ``rc (dotless)`` are generated from the rc registry.
  To bypass compatibility aliases entirely, pass the canonical dotted spellings
  through ``rc_kw``.

Visual alias explorer
---------------------

Use the interactive diagram below to discover which aliases apply to different
parts of your plot:

* **Hover or Focus:** Target a labeled part of the figure to preview its aliases.
* **Click:** Select a label to keep that area highlighted and filter the complete mapping table below.
* **Learn More:** Click the API link in the detail panel to view the canonical documentation.


.. raw:: html

   <div class="uplt-alias-explorer" aria-label="Interactive UltraPlot alias map">
     <div class="uplt-alias-summary" aria-live="polite">
       <span><strong data-alias-total>0</strong> accepted spellings</span>
       <span><strong data-alias-context-total>0</strong> contexts</span>
       <span>one canonical API</span>
     </div>

     <div class="uplt-alias-map-layout">
       <div class="uplt-alias-visual-column">
        <div class="uplt-alias-map" aria-label="Annotated UltraPlot figure">
         <svg viewBox="0 0 760 520" role="img" aria-labelledby="uplt-alias-map-title uplt-alias-map-desc">
           <title id="uplt-alias-map-title">Alias locations on an UltraPlot figure</title>
           <desc id="uplt-alias-map-desc">An annotated chart with interactive labels for figure layout, side titles, axes, plot data, artist style, legend, and colorbar aliases.</desc>
           <image class="uplt-alias-real-figure" href="_static/alias-map.svg" x="20" y="16" width="720" height="427" preserveAspectRatio="xMidYMid meet"/>

           <rect class="uplt-alias-target" data-alias-target="layout" x="20" y="16" width="720" height="427" rx="8"/>
           <g class="uplt-alias-target" data-alias-target="titles">
             <rect x="23" y="44" width="48" height="356" rx="5"/>
             <rect x="688" y="44" width="48" height="356" rx="5"/>
             <rect x="105" y="19" width="528" height="55" rx="5"/>
           </g>
           <rect class="uplt-alias-target" data-alias-target="axes" x="116" y="67" width="514" height="326" rx="5"/>
           <path class="uplt-alias-target uplt-alias-target-line" data-alias-target="plot" d="M120 345 C192 170 236 359 326 286 S449 98 623 182"/>
           <g class="uplt-alias-target" data-alias-target="style">
             <circle cx="121" cy="338" r="13"/><circle cx="325" cy="279" r="13"/><circle cx="511" cy="119" r="13"/><circle cx="623" cy="174" r="13"/>
           </g>
           <rect class="uplt-alias-target" data-alias-target="legend" x="501" y="64" width="128" height="68" rx="4"/>
           <rect class="uplt-alias-target" data-alias-target="colorbar" x="643" y="98" width="38" height="260" rx="4"/>
           <rect class="uplt-alias-target" data-alias-target="inset" x="151" y="101" width="143" height="112" rx="4"/>

           <g class="uplt-alias-node" role="button" tabindex="0" transform="translate(436.3 -38)" data-layout-key="layout" data-anchor-x="380" data-anchor-y="64" data-contexts="figure.init,gridspec,subplot,inset" data-targets="layout,inset" data-label="Figure &amp; layout" data-api="api/ultraplot.figure.Figure.html">
             <path class="uplt-alias-wire" d="M29.0 52.5 L-56.3 102.0"/>
             <rect width="146" height="54" rx="14"/><text x="73" y="22">Figure &amp;</text><text x="73" y="41">layout</text>
           </g>
           <g class="uplt-alias-node" role="button" tabindex="0" transform="translate(-34.9 -34.9)" data-layout-key="titles" data-anchor-x="71" data-anchor-y="64" data-contexts="axes.format,figure.format" data-targets="titles" data-label="Side titles &amp; labels" data-api="api/ultraplot.figure.Figure.html#ultraplot.figure.Figure.format">
             <path class="uplt-alias-wire" d="M84.1 51.3 L105.9 98.9"/>
             <rect width="146" height="54" rx="14"/><text x="73" y="22">Side titles</text><text x="73" y="41">&amp; labels</text>
           </g>
           <g class="uplt-alias-node" role="button" tabindex="0" transform="translate(106.5 469.8)" data-layout-key="axes" data-anchor-x="235" data-anchor-y="393" data-contexts="cartesian.format,geo.format,polar.format,taylor.format,projection" data-targets="axes" data-label="Axes &amp; projections" data-api="api/ultraplot.axes.CartesianAxes.html#ultraplot.axes.CartesianAxes.format">
             <path class="uplt-alias-wire" d="M102.8 2.9 L128.5 -76.8"/>
             <rect width="190" height="54" rx="14"/><text x="95" y="22">Axes &amp;</text><text x="95" y="41">projections</text>
           </g>
           <g class="uplt-alias-node" role="button" tabindex="0" transform="translate(450.3 297.1)" data-layout-key="plot" data-anchor-x="326" data-anchor-y="286" data-contexts="plot.*" data-targets="plot" data-label="Plot methods" data-api="api/ultraplot.axes.PlotAxes.html">
             <path class="uplt-alias-wire" d="M2.9 12.6 L-124.3 -11.1"/>
             <rect width="160" height="54" rx="14"/><text x="80" y="33">Plot methods</text>
           </g>
           <g class="uplt-alias-node" role="button" tabindex="0" transform="translate(625.2 -28)" data-layout-key="legend" data-anchor-x="610" data-anchor-y="64" data-contexts="legend" data-targets="legend" data-label="Legend" data-api="api/ultraplot.axes.Axes.html#ultraplot.axes.Axes.legend">
             <path class="uplt-alias-wire" d="M35.2 52.1 L-15.2 92.0"/>
             <rect width="134" height="54" rx="14"/><text x="67" y="33">Legend</text>
           </g>
           <g class="uplt-alias-node" role="button" tabindex="0" transform="translate(610.1 425.8)" data-layout-key="colorbar" data-anchor-x="662" data-anchor-y="358" data-contexts="colorbar" data-targets="colorbar" data-label="Colorbar" data-api="api/ultraplot.axes.Axes.html#ultraplot.axes.Axes.colorbar">
             <path class="uplt-alias-wire" d="M63.2 3.0 L51.9 -67.8"/>
             <rect width="134" height="54" rx="14"/><text x="67" y="33">Colorbar</text>
           </g>
           <g class="uplt-alias-node" role="button" tabindex="0" transform="translate(-52.2 398.1)" data-layout-key="style" data-anchor-x="121" data-anchor-y="351" data-contexts="style.*" data-targets="style" data-label="Artist styling" data-api="api/ultraplot.axes.PlotAxes.html">
             <path class="uplt-alias-wire" d="M107.1 1.8 L173.2 -47.1"/>
             <rect width="146" height="54" rx="14"/><text x="73" y="33">Artist styling</text>
           </g>
         </svg>
        </div>

        <div class="uplt-alias-categories" aria-label="Alias categories">
         <button type="button" data-contexts="figure.init,figure.format,gridspec,subplot,inset" data-targets="layout,inset,titles" data-label="Figure &amp; layout" data-api="api/ultraplot.figure.Figure.html"><span>▦</span>Figure &amp; layout</button>
         <button type="button" data-contexts="axes.format,cartesian.format,geo.format,polar.format,taylor.format" data-targets="axes,titles" data-label="Axes formatting" data-api="api/ultraplot.axes.Axes.html#ultraplot.axes.Axes.format"><span>⌗</span>Axes formatting</button>
         <button type="button" data-contexts="colorbar,legend" data-targets="colorbar,legend" data-label="Guides" data-api="api/ultraplot.axes.Axes.html"><span>◫</span>Guides</button>
         <button type="button" data-contexts="plot.*" data-targets="plot" data-label="Plot methods" data-api="api/ultraplot.axes.PlotAxes.html"><span>⌁</span>Plot methods</button>
         <button type="button" data-contexts="style.*" data-targets="style" data-label="Artist properties" data-api="api/ultraplot.axes.PlotAxes.html"><span>✦</span>Artist properties</button>
         <button type="button" data-contexts="cycle,projection,scale.*" data-targets="axes,style" data-label="Constructors" data-api="api.html#constructor-functions"><span>⚙</span>Constructors</button>
         <button type="button" data-contexts="rc (dotless)" data-targets="layout,axes,titles,plot,style,legend,colorbar,inset" data-label="Configuration" data-api="api/ultraplot.config.Configurator.html"><span>⋮</span>Configuration</button>
        </div>

        <div class="uplt-alias-filter">
          <label for="uplt-alias-search">Find an accepted or canonical spelling</label>
          <div>
            <input id="uplt-alias-search" type="search" placeholder="Try lw, linewidth, proj, or title…" autocomplete="off"/>
            <button type="button" data-alias-reset>Show all</button>
          </div>
          <p data-alias-filter-status aria-live="polite"></p>
        </div>
       </div>

       <aside class="uplt-alias-detail" aria-live="polite">
         <p class="uplt-alias-detail-help">Drag labels to arrange the map. Hover to preview aliases, or click to keep a selection.</p>
         <h3 data-alias-detail-title>All aliases</h3>
         <p data-alias-detail-copy>Select a labelled region or a category below.</p>
         <div class="uplt-alias-preview" data-alias-preview></div>
         <a class="uplt-alias-api-link" data-alias-api hidden>Open canonical API <span aria-hidden="true">→</span></a>
       </aside>
     </div>
   </div>

.. alias-table-start

Function keyword aliases
------------------------

These mappings apply only in the listed call context.

=================== ================= ==================
Context             Accepted spelling Canonical spelling
=================== ================= ==================
figure.init         ref               refnum
figure.init         aspect            refaspect
figure.init         axwidth           refwidth
figure.init         axheight          refheight
figure.init         width             figwidth
figure.init         height            figheight
axes.format         ltitle            lefttitle
axes.format         ctitle            centertitle
axes.format         rtitle            righttitle
axes.format         ultitle           upperlefttitle
axes.format         uctitle           uppercentertitle
axes.format         urtitle           upperrighttitle
axes.format         lltitle           lowerlefttitle
axes.format         lctitle           lowercentertitle
axes.format         lrtitle           lowerrighttitle
cartesian.format    xloc              xspineloc
cartesian.format    yloc              yspineloc
cartesian.format    xticklabels       xformatter
cartesian.format    yticklabels       yformatter
cartesian.format    xticks            xlocator
cartesian.format    yticks            ylocator
cartesian.format    xminorticks       xminorlocator
cartesian.format    yminorticks       yminorlocator
geo.format          lonlines          lonlocator
geo.format          latlines          latlocator
geo.format          lonminorlines     lonminorlocator
geo.format          latminorlines     latminorlocator
geo.format          lonlines_kw       lonlocator_kw
geo.format          latlines_kw       latlocator_kw
geo.format          lonminorlines_kw  lonminorlocator_kw
geo.format          latminorlines_kw  latminorlocator_kw
polar.format        thetalines        thetalocator
polar.format        rlines            rlocator
polar.format        thetaminorlines   thetaminorlocator
polar.format        rminorlines       rminorlocator
polar.format        thetalabels       thetaformatter
polar.format        rlabels           rformatter
taylor.format       corrlines         corrlocator
taylor.format       corrticks         corrlocator
figure.format       figtitle          suptitle
figure.format       llabels           leftlabels
figure.format       rowlabels         leftlabels
figure.format       rlabels           rightlabels
figure.format       blabels           bottomlabels
figure.format       tlabels           toplabels
figure.format       collabels         toplabels
colorbar            location          loc
colorbar            grid              drawedges
colorbar            edges             drawedges
colorbar            shrink            length
colorbar            title             label
colorbar            labelloc          labellocation
colorbar            locator           ticks
colorbar            formatter         format
colorbar            ticklabels        format
colorbar            minorlocator      minorticks
colorbar            c                 color
colorbar            lw                linewidth
colorbar            tickdir           tickdirection
colorbar            frame             frameon
legend              location          loc
legend              ncol              ncols
legend              frame             frameon
gridspec            wratios           width_ratios
gridspec            hratios           height_ratios
subplot             proj              projection
subplot             proj_kw           projection_kw
inset               proj              projection
cycle               N                 samples
projection          lon_0             lon0
projection          lat_0             lat0
scale.log           basex             base
scale.log           basey             base
scale.log           nonposx           nonpos
scale.log           nonposy           nonpos
scale.log           subsx             subs
scale.log           subsy             subs
scale.symlog        basex             base
scale.symlog        basey             base
scale.symlog        linthreshx        linthresh
scale.symlog        linthreshy        linthresh
scale.symlog        linscalex         linscale
scale.symlog        linscaley         linscale
scale.symlog        subsx             subs
scale.symlog        subsy             subs
plot.labels         fmt               formatter
plot.text           c                 color
plot.text           colors            color
plot.text           size              fontsize
plot.contour_labels c                 colors
plot.contour_labels color             colors
plot.contour_labels size              fontsize
plot.error_bars     bars              barstds
plot.error_bars     barstd            barstds
plot.error_bars     barpctile         barpctiles
plot.error_bars     boxes             boxstds
plot.error_bars     boxstd            boxstds
plot.error_bars     boxpctile         boxpctiles
plot.error_shading  shade             shadestds
plot.error_shading  shadestd          shadestds
plot.error_shading  shadepctile       shadepctiles
plot.error_shading  fade              fadestds
plot.error_shading  fadestd           fadestds
plot.error_shading  fadepctile        fadepctiles
plot.colormap       c                 colors
plot.colormap       color             colors
plot.levels         N                 levels
plot.stacked        stack             stacked
plot.statistics     mean              means
plot.statistics     median            medians
plot.boxplot        showmeans         means
plot.boxplot        filled            fill
plot.violinplot     showmeans         means
plot.violinplot     showmedians       medians
plot.hist           width             rwidth
plot.hist           stack             stacked
plot.hist           filled            fill
plot.pie            labelpad          labeldistance
=================== ================= ==================

Artist property aliases
-----------------------

These are Matplotlib-style shorthand properties accepted while styling artists.

================ ================= ==================
Context          Accepted spelling Canonical spelling
================ ================= ==================
style.rgba       r                 red
style.rgba       g                 green
style.rgba       b                 blue
style.rgba       a                 alpha
style.hsla       h                 hue
style.hsla       s                 saturation
style.hsla       c                 saturation
style.hsla       chroma            saturation
style.hsla       l                 luminance
style.hsla       a                 alpha
style.patch      a                 alpha
style.patch      alphas            alpha
style.patch      fa                alpha
style.patch      facealpha         alpha
style.patch      facealphas        alpha
style.patch      fillalpha         alpha
style.patch      fillalphas        alpha
style.patch      c                 color
style.patch      colors            color
style.patch      ec                edgecolor
style.patch      edgecolors        edgecolor
style.patch      fc                facecolor
style.patch      facecolors        facecolor
style.patch      fillcolor         facecolor
style.patch      fillcolors        facecolor
style.patch      h                 hatch
style.patch      hatching          hatch
style.patch      ls                linestyle
style.patch      linestyles        linestyle
style.patch      lw                linewidth
style.patch      linewidths        linewidth
style.patch      ew                linewidth
style.patch      edgewidth         linewidth
style.patch      edgewidths        linewidth
style.patch      z                 zorder
style.patch      zorders           zorder
style.line       a                 alpha
style.line       alphas            alpha
style.line       c                 color
style.line       colors            color
style.line       d                 dashes
style.line       dash              dashes
style.line       ds                drawstyle
style.line       drawstyles        drawstyle
style.line       fs                fillstyle
style.line       fillstyles        fillstyle
style.line       mfs               fillstyle
style.line       markerfillstyle   fillstyle
style.line       markerfillstyles  fillstyle
style.line       ls                linestyle
style.line       linestyles        linestyle
style.line       lw                linewidth
style.line       linewidths        linewidth
style.line       m                 marker
style.line       markers           marker
style.line       s                 markersize
style.line       ms                markersize
style.line       markersizes       markersize
style.line       ew                markeredgewidth
style.line       edgewidth         markeredgewidth
style.line       edgewidths        markeredgewidth
style.line       mew               markeredgewidth
style.line       markeredgewidths  markeredgewidth
style.line       ec                markeredgecolor
style.line       edgecolor         markeredgecolor
style.line       edgecolors        markeredgecolor
style.line       mec               markeredgecolor
style.line       markeredgecolors  markeredgecolor
style.line       fc                markerfacecolor
style.line       facecolor         markerfacecolor
style.line       facecolors        markerfacecolor
style.line       fillcolor         markerfacecolor
style.line       fillcolors        markerfacecolor
style.line       mc                markerfacecolor
style.line       markercolor       markerfacecolor
style.line       markercolors      markerfacecolor
style.line       mfc               markerfacecolor
style.line       markerfacecolors  markerfacecolor
style.line       z                 zorder
style.line       zorders           zorder
style.collection a                 alpha
style.collection alphas            alpha
style.collection c                 colors
style.collection color             colors
style.collection ec                edgecolors
style.collection edgecolor         edgecolors
style.collection mec               edgecolors
style.collection markeredgecolor   edgecolors
style.collection markeredgecolors  edgecolors
style.collection fc                facecolors
style.collection facecolor         facecolors
style.collection fillcolor         facecolors
style.collection fillcolors        facecolors
style.collection mc                facecolors
style.collection markercolor       facecolors
style.collection markercolors      facecolors
style.collection mfc               facecolors
style.collection markerfacecolor   facecolors
style.collection markerfacecolors  facecolors
style.collection ls                linestyles
style.collection linestyle         linestyles
style.collection lw                linewidths
style.collection linewidth         linewidths
style.collection ew                linewidths
style.collection edgewidth         linewidths
style.collection edgewidths        linewidths
style.collection mew               linewidths
style.collection markeredgewidth   linewidths
style.collection markeredgewidths  linewidths
style.collection m                 marker
style.collection markers           marker
style.collection s                 sizes
style.collection ms                sizes
style.collection markersize        sizes
style.collection markersizes       sizes
style.collection z                 zorder
style.collection zorders           zorder
style.text       c                 color
style.text       fontcolor         color
style.text       family            fontfamily
style.text       name              fontfamily
style.text       fontname          fontfamily
style.text       size              fontsize
style.text       stretch           fontstretch
style.text       style             fontstyle
style.text       variant           fontvariant
style.text       weight            fontweight
style.text       fp                fontproperties
style.text       font              fontproperties
style.text       font_properties   fontproperties
style.text       z                 zorder
style.text       zorders           zorder
================ ================= ==================

Dotless rc aliases
------------------

Use the dotted canonical spelling through ``rc_kw`` when avoiding the accepted shorthand.

============ ================================= ==================================
Context      Accepted spelling                 Canonical spelling
============ ================================= ==================================
rc (dotless) _internalclassic_mode             _internal.classic_mode
rc (dotless) abcbbox                           abc.bbox
rc (dotless) abcbboxalpha                      abc.bboxalpha
rc (dotless) abcbboxcolor                      abc.bboxcolor
rc (dotless) abcbboxpad                        abc.bboxpad
rc (dotless) abcbboxstyle                      abc.bboxstyle
rc (dotless) abcborder                         abc.border
rc (dotless) abcborderwidth                    abc.borderwidth
rc (dotless) abccolor                          abc.color
rc (dotless) abcformat                         abc.format
rc (dotless) abcloc                            abc.loc
rc (dotless) abcsize                           abc.size
rc (dotless) abcstyle                          abc.style
rc (dotless) abctitlepad                       abc.titlepad
rc (dotless) abcweight                         abc.weight
rc (dotless) aggpathchunksize                  agg.path.chunksize
rc (dotless) animationbitrate                  animation.bitrate
rc (dotless) animationcodec                    animation.codec
rc (dotless) animationconvert_args             animation.convert_args
rc (dotless) animationconvert_path             animation.convert_path
rc (dotless) animationembed_limit              animation.embed_limit
rc (dotless) animationffmpeg_args              animation.ffmpeg_args
rc (dotless) animationffmpeg_path              animation.ffmpeg_path
rc (dotless) animationframe_format             animation.frame_format
rc (dotless) animationhtml                     animation.html
rc (dotless) animationwriter                   animation.writer
rc (dotless) axes3dautomargin                  axes3d.automargin
rc (dotless) axes3dgrid                        axes3d.grid
rc (dotless) axes3dmouserotationstyle          axes3d.mouserotationstyle
rc (dotless) axes3dtrackballborder             axes3d.trackballborder
rc (dotless) axes3dtrackballsize               axes3d.trackballsize
rc (dotless) axes3dxaxispanecolor              axes3d.xaxis.panecolor
rc (dotless) axes3dyaxispanecolor              axes3d.yaxis.panecolor
rc (dotless) axes3dzaxispanecolor              axes3d.zaxis.panecolor
rc (dotless) axesalpha                         axes.alpha
rc (dotless) axesautolimit_mode                axes.autolimit_mode
rc (dotless) axesaxisbelow                     axes.axisbelow
rc (dotless) axesedgecolor                     axes.edgecolor
rc (dotless) axesfacealpha                     axes.facealpha
rc (dotless) axesfacecolor                     axes.facecolor
rc (dotless) axesformatterlimits               axes.formatter.limits
rc (dotless) axesformattermin_exponent         axes.formatter.min_exponent
rc (dotless) axesformatteroffset_threshold     axes.formatter.offset_threshold
rc (dotless) axesformattertimerotation         axes.formatter.timerotation
rc (dotless) axesformatteruse_locale           axes.formatter.use_locale
rc (dotless) axesformatteruse_mathtext         axes.formatter.use_mathtext
rc (dotless) axesformatteruseoffset            axes.formatter.useoffset
rc (dotless) axesformatterzerotrim             axes.formatter.zerotrim
rc (dotless) axesgrid                          axes.grid
rc (dotless) axesgridaxis                      axes.grid.axis
rc (dotless) axesgridwhich                     axes.grid.which
rc (dotless) axesinbounds                      axes.inbounds
rc (dotless) axeslabelcolor                    axes.labelcolor
rc (dotless) axeslabelpad                      axes.labelpad
rc (dotless) axeslabelsize                     axes.labelsize
rc (dotless) axeslabelweight                   axes.labelweight
rc (dotless) axeslinewidth                     axes.linewidth
rc (dotless) axesmargin                        axes.margin
rc (dotless) axesprop_cycle                    axes.prop_cycle
rc (dotless) axesspinesbottom                  axes.spines.bottom
rc (dotless) axesspinesleft                    axes.spines.left
rc (dotless) axesspinesright                   axes.spines.right
rc (dotless) axesspinestop                     axes.spines.top
rc (dotless) axessticky_edges                  axes.sticky_edges
rc (dotless) axestitlecolor                    axes.titlecolor
rc (dotless) axestitlelocation                 axes.titlelocation
rc (dotless) axestitlepad                      axes.titlepad
rc (dotless) axestitlesize                     axes.titlesize
rc (dotless) axestitleweight                   axes.titleweight
rc (dotless) axestitley                        axes.titley
rc (dotless) axesunicode_minus                 axes.unicode_minus
rc (dotless) axesxmargin                       axes.xmargin
rc (dotless) axesymargin                       axes.ymargin
rc (dotless) axeszmargin                       axes.zmargin
rc (dotless) barbar_labels                     bar.bar_labels
rc (dotless) bordersalpha                      borders.alpha
rc (dotless) borderscolor                      borders.color
rc (dotless) borderslinewidth                  borders.linewidth
rc (dotless) bordersrasterized                 borders.rasterized
rc (dotless) borderszorder                     borders.zorder
rc (dotless) bottomlabelcolor                  bottomlabel.color
rc (dotless) bottomlabelpad                    bottomlabel.pad
rc (dotless) bottomlabelrotation               bottomlabel.rotation
rc (dotless) bottomlabelsharedpad              bottomlabel.sharedpad
rc (dotless) bottomlabelsize                   bottomlabel.size
rc (dotless) bottomlabelweight                 bottomlabel.weight
rc (dotless) boxplotbootstrap                  boxplot.bootstrap
rc (dotless) boxplotboxpropscolor              boxplot.boxprops.color
rc (dotless) boxplotboxpropslinestyle          boxplot.boxprops.linestyle
rc (dotless) boxplotboxpropslinewidth          boxplot.boxprops.linewidth
rc (dotless) boxplotcappropscolor              boxplot.capprops.color
rc (dotless) boxplotcappropslinestyle          boxplot.capprops.linestyle
rc (dotless) boxplotcappropslinewidth          boxplot.capprops.linewidth
rc (dotless) boxplotflierpropscolor            boxplot.flierprops.color
rc (dotless) boxplotflierpropslinestyle        boxplot.flierprops.linestyle
rc (dotless) boxplotflierpropslinewidth        boxplot.flierprops.linewidth
rc (dotless) boxplotflierpropsmarker           boxplot.flierprops.marker
rc (dotless) boxplotflierpropsmarkeredgecolor  boxplot.flierprops.markeredgecolor
rc (dotless) boxplotflierpropsmarkeredgewidth  boxplot.flierprops.markeredgewidth
rc (dotless) boxplotflierpropsmarkerfacecolor  boxplot.flierprops.markerfacecolor
rc (dotless) boxplotflierpropsmarkersize       boxplot.flierprops.markersize
rc (dotless) boxplotmeanline                   boxplot.meanline
rc (dotless) boxplotmeanpropscolor             boxplot.meanprops.color
rc (dotless) boxplotmeanpropslinestyle         boxplot.meanprops.linestyle
rc (dotless) boxplotmeanpropslinewidth         boxplot.meanprops.linewidth
rc (dotless) boxplotmeanpropsmarker            boxplot.meanprops.marker
rc (dotless) boxplotmeanpropsmarkeredgecolor   boxplot.meanprops.markeredgecolor
rc (dotless) boxplotmeanpropsmarkerfacecolor   boxplot.meanprops.markerfacecolor
rc (dotless) boxplotmeanpropsmarkersize        boxplot.meanprops.markersize
rc (dotless) boxplotmedianpropscolor           boxplot.medianprops.color
rc (dotless) boxplotmedianpropslinestyle       boxplot.medianprops.linestyle
rc (dotless) boxplotmedianpropslinewidth       boxplot.medianprops.linewidth
rc (dotless) boxplotnotch                      boxplot.notch
rc (dotless) boxplotpatchartist                boxplot.patchartist
rc (dotless) boxplotshowbox                    boxplot.showbox
rc (dotless) boxplotshowcaps                   boxplot.showcaps
rc (dotless) boxplotshowfliers                 boxplot.showfliers
rc (dotless) boxplotshowmeans                  boxplot.showmeans
rc (dotless) boxplotvertical                   boxplot.vertical
rc (dotless) boxplotwhiskerpropscolor          boxplot.whiskerprops.color
rc (dotless) boxplotwhiskerpropslinestyle      boxplot.whiskerprops.linestyle
rc (dotless) boxplotwhiskerpropslinewidth      boxplot.whiskerprops.linewidth
rc (dotless) boxplotwhiskers                   boxplot.whiskers
rc (dotless) cartopyautoextent                 cartopy.autoextent
rc (dotless) cartopycircular                   cartopy.circular
rc (dotless) cftimemax_display_ticks           cftime.max_display_ticks
rc (dotless) cftimeresolution                  cftime.resolution
rc (dotless) cftimetime_resolution_format      cftime.time_resolution_format
rc (dotless) cftimetime_unit                   cftime.time_unit
rc (dotless) chordend                          chord.end
rc (dotless) chordendspace                     chord.endspace
rc (dotless) chordorder                        chord.order
rc (dotless) chordr_lim                        chord.r_lim
rc (dotless) chordspace                        chord.space
rc (dotless) chordstart                        chord.start
rc (dotless) chordticks_interval               chord.ticks_interval
rc (dotless) cmapautodiverging                 cmap.autodiverging
rc (dotless) cmapcyclic                        cmap.cyclic
rc (dotless) cmapdiscrete                      cmap.discrete
rc (dotless) cmapdiverging                     cmap.diverging
rc (dotless) cmapedgefix                       cmap.edgefix
rc (dotless) cmapinbounds                      cmap.inbounds
rc (dotless) cmaplevels                        cmap.levels
rc (dotless) cmaplistedthresh                  cmap.listedthresh
rc (dotless) cmaplut                           cmap.lut
rc (dotless) cmapqualitative                   cmap.qualitative
rc (dotless) cmaprobust                        cmap.robust
rc (dotless) cmapsequential                    cmap.sequential
rc (dotless) coastalpha                        coast.alpha
rc (dotless) coastcolor                        coast.color
rc (dotless) coastlinewidth                    coast.linewidth
rc (dotless) coastrasterized                   coast.rasterized
rc (dotless) coastzorder                       coast.zorder
rc (dotless) colorbarcenter_levels             colorbar.center_levels
rc (dotless) colorbaredgecolor                 colorbar.edgecolor
rc (dotless) colorbarextend                    colorbar.extend
rc (dotless) colorbarfacecolor                 colorbar.facecolor
rc (dotless) colorbarfancybox                  colorbar.fancybox
rc (dotless) colorbarframealpha                colorbar.framealpha
rc (dotless) colorbarframeon                   colorbar.frameon
rc (dotless) colorbargrid                      colorbar.grid
rc (dotless) colorbarinsetextend               colorbar.insetextend
rc (dotless) colorbarinsetlength               colorbar.insetlength
rc (dotless) colorbarinsetpad                  colorbar.insetpad
rc (dotless) colorbarinsetwidth                colorbar.insetwidth
rc (dotless) colorbarlabelrotation             colorbar.labelrotation
rc (dotless) colorbarlength                    colorbar.length
rc (dotless) colorbarloc                       colorbar.loc
rc (dotless) colorbaroutline                   colorbar.outline
rc (dotless) colorbarrasterize                 colorbar.rasterize
rc (dotless) colorbarrasterized                colorbar.rasterized
rc (dotless) colorbarshadow                    colorbar.shadow
rc (dotless) colorbarwidth                     colorbar.width
rc (dotless) contouralgorithm                  contour.algorithm
rc (dotless) contourcorner_mask                contour.corner_mask
rc (dotless) contourlinewidth                  contour.linewidth
rc (dotless) contournegative_linestyle         contour.negative_linestyle
rc (dotless) curved_quiverarrows_at_end        curved_quiver.arrows_at_end
rc (dotless) curved_quiverarrowsize            curved_quiver.arrowsize
rc (dotless) curved_quiverarrowstyle           curved_quiver.arrowstyle
rc (dotless) curved_quiverdensity              curved_quiver.density
rc (dotless) curved_quivergrains               curved_quiver.grains
rc (dotless) curved_quiverscale                curved_quiver.scale
rc (dotless) dateautoformatterday              date.autoformatter.day
rc (dotless) dateautoformatterhour             date.autoformatter.hour
rc (dotless) dateautoformattermicrosecond      date.autoformatter.microsecond
rc (dotless) dateautoformatterminute           date.autoformatter.minute
rc (dotless) dateautoformattermonth            date.autoformatter.month
rc (dotless) dateautoformattersecond           date.autoformatter.second
rc (dotless) dateautoformatteryear             date.autoformatter.year
rc (dotless) dateconverter                     date.converter
rc (dotless) dateepoch                         date.epoch
rc (dotless) dateinterval_multiples            date.interval_multiples
rc (dotless) docstringhardcopy                 docstring.hardcopy
rc (dotless) errorbarcapsize                   errorbar.capsize
rc (dotless) externalshrink                    external.shrink
rc (dotless) figureautolayout                  figure.autolayout
rc (dotless) figureconstrained_layouth_pad     figure.constrained_layout.h_pad
rc (dotless) figureconstrained_layouthspace    figure.constrained_layout.hspace
rc (dotless) figureconstrained_layoutuse       figure.constrained_layout.use
rc (dotless) figureconstrained_layoutw_pad     figure.constrained_layout.w_pad
rc (dotless) figureconstrained_layoutwspace    figure.constrained_layout.wspace
rc (dotless) figuredpi                         figure.dpi
rc (dotless) figureedgecolor                   figure.edgecolor
rc (dotless) figurefacecolor                   figure.facecolor
rc (dotless) figurefigsize                     figure.figsize
rc (dotless) figureframeon                     figure.frameon
rc (dotless) figurehooks                       figure.hooks
rc (dotless) figurelabelsize                   figure.labelsize
rc (dotless) figurelabelweight                 figure.labelweight
rc (dotless) figuremax_open_warning            figure.max_open_warning
rc (dotless) figureraise_window                figure.raise_window
rc (dotless) figuresubplotbottom               figure.subplot.bottom
rc (dotless) figuresubplothspace               figure.subplot.hspace
rc (dotless) figuresubplotleft                 figure.subplot.left
rc (dotless) figuresubplotright                figure.subplot.right
rc (dotless) figuresubplottop                  figure.subplot.top
rc (dotless) figuresubplotwspace               figure.subplot.wspace
rc (dotless) figuretitlesize                   figure.titlesize
rc (dotless) figuretitleweight                 figure.titleweight
rc (dotless) fontcursive                       font.cursive
rc (dotless) fontfamily                        font.family
rc (dotless) fontfantasy                       font.fantasy
rc (dotless) fontlarge                         font.large
rc (dotless) fontlargesize                     font.largesize
rc (dotless) fontmonospace                     font.monospace
rc (dotless) fontname                          font.name
rc (dotless) fontsans-serif                    font.sans-serif
rc (dotless) fontserif                         font.serif
rc (dotless) fontsize                          font.size
rc (dotless) fontsmall                         font.small
rc (dotless) fontsmallsize                     font.smallsize
rc (dotless) fontstretch                       font.stretch
rc (dotless) fontstyle                         font.style
rc (dotless) fontvariant                       font.variant
rc (dotless) fontweight                        font.weight
rc (dotless) formatterlimits                   formatter.limits
rc (dotless) formatterlog                      formatter.log
rc (dotless) formattermin_exponent             formatter.min_exponent
rc (dotless) formatteroffset_threshold         formatter.offset_threshold
rc (dotless) formattertimerotation             formatter.timerotation
rc (dotless) formatteruse_locale               formatter.use_locale
rc (dotless) formatteruse_mathtext             formatter.use_mathtext
rc (dotless) formatteruse_offset               formatter.use_offset
rc (dotless) formatterzerotrim                 formatter.zerotrim
rc (dotless) geoaxesedgecolor                  geoaxes.edgecolor
rc (dotless) geoaxesfacealpha                  geoaxes.facealpha
rc (dotless) geoaxesfacecolor                  geoaxes.facecolor
rc (dotless) geoaxeslinewidth                  geoaxes.linewidth
rc (dotless) geobackend                        geo.backend
rc (dotless) geochoroplethcountry_reso         geo.choropleth.country_reso
rc (dotless) geochoroplethcountry_territories  geo.choropleth.country_territories
rc (dotless) geochoroplethzorder               geo.choropleth.zorder
rc (dotless) geoextent                         geo.extent
rc (dotless) geogridalpha                      geogrid.alpha
rc (dotless) geogridcolor                      geogrid.color
rc (dotless) geogridlabelpad                   geogrid.labelpad
rc (dotless) geogridlabels                     geogrid.labels
rc (dotless) geogridlabelsize                  geogrid.labelsize
rc (dotless) geogridlatmax                     geogrid.latmax
rc (dotless) geogridlatstep                    geogrid.latstep
rc (dotless) geogridlinestyle                  geogrid.linestyle
rc (dotless) geogridlinewidth                  geogrid.linewidth
rc (dotless) geogridlonstep                    geogrid.lonstep
rc (dotless) georound                          geo.round
rc (dotless) graphaspect                       graph.aspect
rc (dotless) graphdraw_edges                   graph.draw_edges
rc (dotless) graphdraw_grid                    graph.draw_grid
rc (dotless) graphdraw_labels                  graph.draw_labels
rc (dotless) graphdraw_nodes                   graph.draw_nodes
rc (dotless) graphdraw_spines                  graph.draw_spines
rc (dotless) graphfacecolor                    graph.facecolor
rc (dotless) graphrescale                      graph.rescale
rc (dotless) gridalpha                         grid.alpha
rc (dotless) gridbelow                         grid.below
rc (dotless) gridcheckoverlap                  grid.checkoverlap
rc (dotless) gridcolor                         grid.color
rc (dotless) griddmslabels                     grid.dmslabels
rc (dotless) gridgeolabels                     grid.geolabels
rc (dotless) gridinlinelabels                  grid.inlinelabels
rc (dotless) gridlabelcolor                    grid.labelcolor
rc (dotless) gridlabelpad                      grid.labelpad
rc (dotless) gridlabels                        grid.labels
rc (dotless) gridlabelsize                     grid.labelsize
rc (dotless) gridlabelweight                   grid.labelweight
rc (dotless) gridlatinline                     grid.latinline
rc (dotless) gridlinestyle                     grid.linestyle
rc (dotless) gridlinewidth                     grid.linewidth
rc (dotless) gridloninline                     grid.loninline
rc (dotless) gridminoralpha                    gridminor.alpha
rc (dotless) gridminorcolor                    gridminor.color
rc (dotless) gridminorlatstep                  gridminor.latstep
rc (dotless) gridminorlinestyle                gridminor.linestyle
rc (dotless) gridminorlinewidth                gridminor.linewidth
rc (dotless) gridminorlonstep                  gridminor.lonstep
rc (dotless) gridminorstyle                    gridminor.style
rc (dotless) gridminorwidth                    gridminor.width
rc (dotless) gridnsteps                        grid.nsteps
rc (dotless) gridpad                           grid.pad
rc (dotless) gridratio                         grid.ratio
rc (dotless) gridrotatelabels                  grid.rotatelabels
rc (dotless) gridstyle                         grid.style
rc (dotless) gridwidth                         grid.width
rc (dotless) gridwidthratio                    grid.widthratio
rc (dotless) hatchcolor                        hatch.color
rc (dotless) hatchlinewidth                    hatch.linewidth
rc (dotless) histbins                          hist.bins
rc (dotless) imageaspect                       image.aspect
rc (dotless) imagecmap                         image.cmap
rc (dotless) imagecomposite_image              image.composite_image
rc (dotless) imagediscrete                     image.discrete
rc (dotless) imageedgefix                      image.edgefix
rc (dotless) imageinbounds                     image.inbounds
rc (dotless) imageinterpolation                image.interpolation
rc (dotless) imageinterpolation_stage          image.interpolation_stage
rc (dotless) imagelevels                       image.levels
rc (dotless) imagelut                          image.lut
rc (dotless) imageorigin                       image.origin
rc (dotless) imageresample                     image.resample
rc (dotless) innerbordersalpha                 innerborders.alpha
rc (dotless) innerborderscolor                 innerborders.color
rc (dotless) innerborderslinewidth             innerborders.linewidth
rc (dotless) innerborderszorder                innerborders.zorder
rc (dotless) kdepoints                         kde.points
rc (dotless) keymapback                        keymap.back
rc (dotless) keymapcopy                        keymap.copy
rc (dotless) keymapforward                     keymap.forward
rc (dotless) keymapfullscreen                  keymap.fullscreen
rc (dotless) keymapgrid                        keymap.grid
rc (dotless) keymapgrid_minor                  keymap.grid_minor
rc (dotless) keymaphelp                        keymap.help
rc (dotless) keymaphome                        keymap.home
rc (dotless) keymappan                         keymap.pan
rc (dotless) keymapquit                        keymap.quit
rc (dotless) keymapquit_all                    keymap.quit_all
rc (dotless) keymapsave                        keymap.save
rc (dotless) keymapxscale                      keymap.xscale
rc (dotless) keymapyscale                      keymap.yscale
rc (dotless) keymapzoom                        keymap.zoom
rc (dotless) labelcolor                        label.color
rc (dotless) labelpad                          label.pad
rc (dotless) labelsize                         label.size
rc (dotless) labelweight                       label.weight
rc (dotless) lakesalpha                        lakes.alpha
rc (dotless) lakescolor                        lakes.color
rc (dotless) lakesrasterized                   lakes.rasterized
rc (dotless) lakeszorder                       lakes.zorder
rc (dotless) landalpha                         land.alpha
rc (dotless) landcolor                         land.color
rc (dotless) landrasterized                    land.rasterized
rc (dotless) landzorder                        land.zorder
rc (dotless) leftlabelcolor                    leftlabel.color
rc (dotless) leftlabelpad                      leftlabel.pad
rc (dotless) leftlabelrotation                 leftlabel.rotation
rc (dotless) leftlabelsharedpad                leftlabel.sharedpad
rc (dotless) leftlabelsize                     leftlabel.size
rc (dotless) leftlabelweight                   leftlabel.weight
rc (dotless) legendborderaxespad               legend.borderaxespad
rc (dotless) legendborderpad                   legend.borderpad
rc (dotless) legendcatalpha                    legend.cat.alpha
rc (dotless) legendcatline                     legend.cat.line
rc (dotless) legendcatlinestyle                legend.cat.linestyle
rc (dotless) legendcatlinewidth                legend.cat.linewidth
rc (dotless) legendcatmarker                   legend.cat.marker
rc (dotless) legendcatmarkeredgecolor          legend.cat.markeredgecolor
rc (dotless) legendcatmarkeredgewidth          legend.cat.markeredgewidth
rc (dotless) legendcatmarkersize               legend.cat.markersize
rc (dotless) legendcolumnspacing               legend.columnspacing
rc (dotless) legendedgecolor                   legend.edgecolor
rc (dotless) legendfacecolor                   legend.facecolor
rc (dotless) legendfancybox                    legend.fancybox
rc (dotless) legendfontsize                    legend.fontsize
rc (dotless) legendframealpha                  legend.framealpha
rc (dotless) legendframeon                     legend.frameon
rc (dotless) legendgeoalpha                    legend.geo.alpha
rc (dotless) legendgeocountry_proj             legend.geo.country_proj
rc (dotless) legendgeocountry_reso             legend.geo.country_reso
rc (dotless) legendgeocountry_territories      legend.geo.country_territories
rc (dotless) legendgeoedgecolor                legend.geo.edgecolor
rc (dotless) legendgeofacecolor                legend.geo.facecolor
rc (dotless) legendgeofill                     legend.geo.fill
rc (dotless) legendgeohandlesize               legend.geo.handlesize
rc (dotless) legendgeolinewidth                legend.geo.linewidth
rc (dotless) legendhandleheight                legend.handleheight
rc (dotless) legendhandlelength                legend.handlelength
rc (dotless) legendhandletextpad               legend.handletextpad
rc (dotless) legendlabelcolor                  legend.labelcolor
rc (dotless) legendlabelspacing                legend.labelspacing
rc (dotless) legendloc                         legend.loc
rc (dotless) legendmarkerscale                 legend.markerscale
rc (dotless) legendnumalpha                    legend.num.alpha
rc (dotless) legendnumcmap                     legend.num.cmap
rc (dotless) legendnumedgecolor                legend.num.edgecolor
rc (dotless) legendnumformat                   legend.num.format
rc (dotless) legendnumlinewidth                legend.num.linewidth
rc (dotless) legendnumn                        legend.num.n
rc (dotless) legendnumpoints                   legend.numpoints
rc (dotless) legendscatterpoints               legend.scatterpoints
rc (dotless) legendshadow                      legend.shadow
rc (dotless) legendsizealpha                   legend.size.alpha
rc (dotless) legendsizearea                    legend.size.area
rc (dotless) legendsizecolor                   legend.size.color
rc (dotless) legendsizeformat                  legend.size.format
rc (dotless) legendsizemarker                  legend.size.marker
rc (dotless) legendsizemarkeredgecolor         legend.size.markeredgecolor
rc (dotless) legendsizemarkeredgewidth         legend.size.markeredgewidth
rc (dotless) legendsizeminsize                 legend.size.minsize
rc (dotless) legendsizescale                   legend.size.scale
rc (dotless) legendtitle_fontsize              legend.title_fontsize
rc (dotless) linesantialiased                  lines.antialiased
rc (dotless) linescolor                        lines.color
rc (dotless) linesdash_capstyle                lines.dash_capstyle
rc (dotless) linesdash_joinstyle               lines.dash_joinstyle
rc (dotless) linesdashdot_pattern              lines.dashdot_pattern
rc (dotless) linesdashed_pattern               lines.dashed_pattern
rc (dotless) linesdotted_pattern               lines.dotted_pattern
rc (dotless) lineslinestyle                    lines.linestyle
rc (dotless) lineslinewidth                    lines.linewidth
rc (dotless) linesmarker                       lines.marker
rc (dotless) linesmarkeredgecolor              lines.markeredgecolor
rc (dotless) linesmarkeredgewidth              lines.markeredgewidth
rc (dotless) linesmarkerfacecolor              lines.markerfacecolor
rc (dotless) linesmarkersize                   lines.markersize
rc (dotless) linesscale_dashes                 lines.scale_dashes
rc (dotless) linessolid_capstyle               lines.solid_capstyle
rc (dotless) linessolid_joinstyle              lines.solid_joinstyle
rc (dotless) lollipopmarkersize                lollipop.markersize
rc (dotless) lollipopstemcolor                 lollipop.stemcolor
rc (dotless) lollipopstemlinestyle             lollipop.stemlinestyle
rc (dotless) lollipopstemwidth                 lollipop.stemwidth
rc (dotless) macosxwindow_mode                 macosx.window_mode
rc (dotless) markersfillstyle                  markers.fillstyle
rc (dotless) mathtextbf                        mathtext.bf
rc (dotless) mathtextbfit                      mathtext.bfit
rc (dotless) mathtextcal                       mathtext.cal
rc (dotless) mathtextcm_symbols                mathtext.cm_symbols
rc (dotless) mathtextdefault                   mathtext.default
rc (dotless) mathtextfallback                  mathtext.fallback
rc (dotless) mathtextfontset                   mathtext.fontset
rc (dotless) mathtextit                        mathtext.it
rc (dotless) mathtextrm                        mathtext.rm
rc (dotless) mathtextsf                        mathtext.sf
rc (dotless) mathtexttt                        mathtext.tt
rc (dotless) metacolor                         meta.color
rc (dotless) metaedgecolor                     meta.edgecolor
rc (dotless) metalinewidth                     meta.linewidth
rc (dotless) metawidth                         meta.width
rc (dotless) navigationpreview                 navigation.preview
rc (dotless) oceanalpha                        ocean.alpha
rc (dotless) oceancolor                        ocean.color
rc (dotless) oceanrasterized                   ocean.rasterized
rc (dotless) oceanzorder                       ocean.zorder
rc (dotless) patchantialiased                  patch.antialiased
rc (dotless) patchedgecolor                    patch.edgecolor
rc (dotless) patchfacecolor                    patch.facecolor
rc (dotless) patchforce_edgecolor              patch.force_edgecolor
rc (dotless) patchlinewidth                    patch.linewidth
rc (dotless) patheffects                       path.effects
rc (dotless) pathsimplify                      path.simplify
rc (dotless) pathsimplify_threshold            path.simplify_threshold
rc (dotless) pathsketch                        path.sketch
rc (dotless) pathsnap                          path.snap
rc (dotless) pcolormeshsnap                    pcolormesh.snap
rc (dotless) pcolorshading                     pcolor.shading
rc (dotless) pdfcompression                    pdf.compression
rc (dotless) pdffonttype                       pdf.fonttype
rc (dotless) pdfinheritcolor                   pdf.inheritcolor
rc (dotless) pdfuse14corefonts                 pdf.use14corefonts
rc (dotless) pgfpreamble                       pgf.preamble
rc (dotless) pgfrcfonts                        pgf.rcfonts
rc (dotless) pgftexsystem                      pgf.texsystem
rc (dotless) phylogenyalign_leaf_label         phylogeny.align_leaf_label
rc (dotless) phylogenyend                      phylogeny.end
rc (dotless) phylogenyformat                   phylogeny.format
rc (dotless) phylogenyignore_branch_length     phylogeny.ignore_branch_length
rc (dotless) phylogenyladderize                phylogeny.ladderize
rc (dotless) phylogenyleaf_label_rmargin       phylogeny.leaf_label_rmargin
rc (dotless) phylogenyleaf_label_size          phylogeny.leaf_label_size
rc (dotless) phylogenyouter                    phylogeny.outer
rc (dotless) phylogenyr_lim                    phylogeny.r_lim
rc (dotless) phylogenyreverse                  phylogeny.reverse
rc (dotless) phylogenystart                    phylogeny.start
rc (dotless) polaraxesgrid                     polaraxes.grid
rc (dotless) psdistillerres                    ps.distiller.res
rc (dotless) psfonttype                        ps.fonttype
rc (dotless) pspapersize                       ps.papersize
rc (dotless) psuseafm                          ps.useafm
rc (dotless) psusedistiller                    ps.usedistiller
rc (dotless) radarbg_color                     radar.bg_color
rc (dotless) radarcircular                     radar.circular
rc (dotless) radarfill                         radar.fill
rc (dotless) radargrid_interval_ratio          radar.grid_interval_ratio
rc (dotless) radarmarker_size                  radar.marker_size
rc (dotless) radarr_lim                        radar.r_lim
rc (dotless) radarshow_grid_label              radar.show_grid_label
rc (dotless) radarvmax                         radar.vmax
rc (dotless) radarvmin                         radar.vmin
rc (dotless) ribbonflowalpha                   ribbon.flow.alpha
rc (dotless) ribbonflowcurvature               ribbon.flow.curvature
rc (dotless) ribbonnodewidth                   ribbon.nodewidth
rc (dotless) ribbonrowheightratio              ribbon.rowheightratio
rc (dotless) ribbontopic_label_box             ribbon.topic_label_box
rc (dotless) ribbontopic_label_offset          ribbon.topic_label_offset
rc (dotless) ribbontopic_label_size            ribbon.topic_label_size
rc (dotless) ribbontopic_labels                ribbon.topic_labels
rc (dotless) ribbonxmargin                     ribbon.xmargin
rc (dotless) ribbonymargin                     ribbon.ymargin
rc (dotless) rightlabelcolor                   rightlabel.color
rc (dotless) rightlabelpad                     rightlabel.pad
rc (dotless) rightlabelrotation                rightlabel.rotation
rc (dotless) rightlabelsharedpad               rightlabel.sharedpad
rc (dotless) rightlabelsize                    rightlabel.size
rc (dotless) rightlabelweight                  rightlabel.weight
rc (dotless) riversalpha                       rivers.alpha
rc (dotless) riverscolor                       rivers.color
rc (dotless) riverslinewidth                   rivers.linewidth
rc (dotless) riversrasterized                  rivers.rasterized
rc (dotless) riverszorder                      rivers.zorder
rc (dotless) sankeyalign                       sankey.align
rc (dotless) sankeyconnect                     sankey.connect
rc (dotless) sankeyflow_label_pos              sankey.flow_label_pos
rc (dotless) sankeyflow_labels                 sankey.flow_labels
rc (dotless) sankeyflow_sort                   sankey.flow_sort
rc (dotless) sankeyflowalpha                   sankey.flow.alpha
rc (dotless) sankeyflowcurvature               sankey.flow.curvature
rc (dotless) sankeymargin                      sankey.margin
rc (dotless) sankeynode_label_offset           sankey.node_label_offset
rc (dotless) sankeynode_label_outside          sankey.node_label_outside
rc (dotless) sankeynode_labels                 sankey.node_labels
rc (dotless) sankeynodefacecolor               sankey.node.facecolor
rc (dotless) sankeynodepad                     sankey.nodepad
rc (dotless) sankeynodewidth                   sankey.nodewidth
rc (dotless) sankeyother_label                 sankey.other_label
rc (dotless) sankeypathlabel                   sankey.pathlabel
rc (dotless) sankeypathlengths                 sankey.pathlengths
rc (dotless) sankeyrotation                    sankey.rotation
rc (dotless) sankeytrunklength                 sankey.trunklength
rc (dotless) savefigbbox                       savefig.bbox
rc (dotless) savefigdirectory                  savefig.directory
rc (dotless) savefigdpi                        savefig.dpi
rc (dotless) savefigedgecolor                  savefig.edgecolor
rc (dotless) savefigfacecolor                  savefig.facecolor
rc (dotless) savefigformat                     savefig.format
rc (dotless) savefigorientation                savefig.orientation
rc (dotless) savefigpad_inches                 savefig.pad_inches
rc (dotless) savefigtransparent                savefig.transparent
rc (dotless) scatteredgecolors                 scatter.edgecolors
rc (dotless) scattermarker                     scatter.marker
rc (dotless) subplotsalign                     subplots.align
rc (dotless) subplotsaxpad                     subplots.axpad
rc (dotless) subplotsaxwidth                   subplots.axwidth
rc (dotless) subplotsequalspace                subplots.equalspace
rc (dotless) subplotsgroupspace                subplots.groupspace
rc (dotless) subplotsinnerpad                  subplots.innerpad
rc (dotless) subplotsouterpad                  subplots.outerpad
rc (dotless) subplotspad                       subplots.pad
rc (dotless) subplotspanelpad                  subplots.panelpad
rc (dotless) subplotspanelwidth                subplots.panelwidth
rc (dotless) subplotspixelsnap                 subplots.pixelsnap
rc (dotless) subplotsrefwidth                  subplots.refwidth
rc (dotless) subplotsshare                     subplots.share
rc (dotless) subplotsspan                      subplots.span
rc (dotless) subplotstight                     subplots.tight
rc (dotless) suptitlecolor                     suptitle.color
rc (dotless) suptitlepad                       suptitle.pad
rc (dotless) suptitlesize                      suptitle.size
rc (dotless) suptitleweight                    suptitle.weight
rc (dotless) svgfonttype                       svg.fonttype
rc (dotless) svghashsalt                       svg.hashsalt
rc (dotless) svgid                             svg.id
rc (dotless) svgimage_inline                   svg.image_inline
rc (dotless) textalign                         text.align
rc (dotless) textalignarrows                   text.align.arrows
rc (dotless) textalignmaxiter                  text.align.maxiter
rc (dotless) textalignpad                      text.align.pad
rc (dotless) textantialiased                   text.antialiased
rc (dotless) textborderstyle                   text.borderstyle
rc (dotless) textcolor                         text.color
rc (dotless) textcurvedavoid_overlap           text.curved.avoid_overlap
rc (dotless) textcurvedcurvature_pad           text.curved.curvature_pad
rc (dotless) textcurvedellipsis                text.curved.ellipsis
rc (dotless) textcurvedmin_advance             text.curved.min_advance
rc (dotless) textcurvedoverlap_tol             text.curved.overlap_tol
rc (dotless) textcurvedupright                 text.curved.upright
rc (dotless) texthinting                       text.hinting
rc (dotless) texthinting_factor                text.hinting_factor
rc (dotless) textkerning_factor                text.kerning_factor
rc (dotless) textlabelsize                     text.labelsize
rc (dotless) textlatexpreamble                 text.latex.preamble
rc (dotless) textparse_math                    text.parse_math
rc (dotless) texttitlesize                     text.titlesize
rc (dotless) textusetex                        text.usetex
rc (dotless) tickcolor                         tick.color
rc (dotless) tickdir                           tick.dir
rc (dotless) ticklabelcolor                    tick.labelcolor
rc (dotless) ticklabelpad                      tick.labelpad
rc (dotless) ticklabelsize                     tick.labelsize
rc (dotless) ticklabelweight                   tick.labelweight
rc (dotless) ticklen                           tick.len
rc (dotless) ticklenratio                      tick.lenratio
rc (dotless) ticklinewidth                     tick.linewidth
rc (dotless) tickminor                         tick.minor
rc (dotless) tickpad                           tick.pad
rc (dotless) tickratio                         tick.ratio
rc (dotless) tickwidth                         tick.width
rc (dotless) tickwidthratio                    tick.widthratio
rc (dotless) titleabove                        title.above
rc (dotless) titlebbox                         title.bbox
rc (dotless) titlebboxalpha                    title.bboxalpha
rc (dotless) titlebboxcolor                    title.bboxcolor
rc (dotless) titlebboxpad                      title.bboxpad
rc (dotless) titlebboxstyle                    title.bboxstyle
rc (dotless) titleborder                       title.border
rc (dotless) titleborderwidth                  title.borderwidth
rc (dotless) titlecolor                        title.color
rc (dotless) titleloc                          title.loc
rc (dotless) titlepad                          title.pad
rc (dotless) titlesize                         title.size
rc (dotless) titleweight                       title.weight
rc (dotless) tkwindow_focus                    tk.window_focus
rc (dotless) toplabelcolor                     toplabel.color
rc (dotless) toplabelpad                       toplabel.pad
rc (dotless) toplabelrotation                  toplabel.rotation
rc (dotless) toplabelsharedpad                 toplabel.sharedpad
rc (dotless) toplabelsize                      toplabel.size
rc (dotless) toplabelweight                    toplabel.weight
rc (dotless) ultraplotcheck_for_latest_version ultraplot.check_for_latest_version
rc (dotless) ultraploteager_import             ultraplot.eager_import
rc (dotless) webaggaddress                     webagg.address
rc (dotless) webaggopen_in_browser             webagg.open_in_browser
rc (dotless) webaggport                        webagg.port
rc (dotless) webaggport_retries                webagg.port_retries
rc (dotless) xaxislabellocation                xaxis.labellocation
rc (dotless) xtickalignment                    xtick.alignment
rc (dotless) xtickbottom                       xtick.bottom
rc (dotless) xtickcolor                        xtick.color
rc (dotless) xtickdirection                    xtick.direction
rc (dotless) xticklabelbottom                  xtick.labelbottom
rc (dotless) xticklabelcolor                   xtick.labelcolor
rc (dotless) xticklabelsize                    xtick.labelsize
rc (dotless) xticklabeltop                     xtick.labeltop
rc (dotless) xtickmajorbottom                  xtick.major.bottom
rc (dotless) xtickmajorpad                     xtick.major.pad
rc (dotless) xtickmajorsize                    xtick.major.size
rc (dotless) xtickmajortop                     xtick.major.top
rc (dotless) xtickmajorwidth                   xtick.major.width
rc (dotless) xtickminorbottom                  xtick.minor.bottom
rc (dotless) xtickminorndivs                   xtick.minor.ndivs
rc (dotless) xtickminorpad                     xtick.minor.pad
rc (dotless) xtickminorsize                    xtick.minor.size
rc (dotless) xtickminortop                     xtick.minor.top
rc (dotless) xtickminorvisible                 xtick.minor.visible
rc (dotless) xtickminorwidth                   xtick.minor.width
rc (dotless) xticktop                          xtick.top
rc (dotless) yaxislabellocation                yaxis.labellocation
rc (dotless) ytickalignment                    ytick.alignment
rc (dotless) ytickcolor                        ytick.color
rc (dotless) ytickdirection                    ytick.direction
rc (dotless) yticklabelcolor                   ytick.labelcolor
rc (dotless) yticklabelleft                    ytick.labelleft
rc (dotless) yticklabelright                   ytick.labelright
rc (dotless) yticklabelsize                    ytick.labelsize
rc (dotless) ytickleft                         ytick.left
rc (dotless) ytickmajorleft                    ytick.major.left
rc (dotless) ytickmajorpad                     ytick.major.pad
rc (dotless) ytickmajorright                   ytick.major.right
rc (dotless) ytickmajorsize                    ytick.major.size
rc (dotless) ytickmajorwidth                   ytick.major.width
rc (dotless) ytickminorleft                    ytick.minor.left
rc (dotless) ytickminorndivs                   ytick.minor.ndivs
rc (dotless) ytickminorpad                     ytick.minor.pad
rc (dotless) ytickminorright                   ytick.minor.right
rc (dotless) ytickminorsize                    ytick.minor.size
rc (dotless) ytickminorvisible                 ytick.minor.visible
rc (dotless) ytickminorwidth                   ytick.minor.width
rc (dotless) ytickright                        ytick.right
============ ================================= ==================================

.. alias-table-end

Supplying a legacy and canonical spelling together is an error. For example,
``ax.format(xlocator=5, xticks=10)`` does not silently choose one value.
