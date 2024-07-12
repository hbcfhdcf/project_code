#
# Copyright 2019-2020 Thomas Kramer.
#
# This source describes Open Hardware and is licensed under the CERN-OHL-S v2.
#
# You may redistribute and modify this documentation and make products using it
# under the terms of the CERN-OHL-S v2 (https:/cern.ch/cern-ohl).
# This documentation is distributed WITHOUT ANY EXPRESS OR IMPLIED WARRANTY,
# INCLUDING OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS FOR A PARTICULAR PURPOSE.
# Please see the CERN-OHL-S v2 for applicable conditions.
#
# Source location: https://codeberg.org/tok/librecell
#
import logging
from typing import Dict, List, Tuple
from klayout import db

import lef_types as lef

logger = logging.getLogger(__name__)


def _decompose_region(region: db.Region, ignore_non_rectilinear: bool = False) -> List[db.Box]:
    """
    Decompose a `db.Region` of multiple `db.Polygon`s into non-overlapping rectangles (`db.Box`).
    :param region:
    :param ignore_non_rectilinear: If set to `True` then non-rectilinear polygons are skipped.
    :return: Returns the list of rectangles.
    """
    trapezoids = region.decompose_trapezoids_to_region()
    logger.debug("Number of trapezoids: {}".format(trapezoids.size()))
    rectangles = []
    for polygon in trapezoids.each():
        box = polygon.bbox()

        if db.Polygon(box) != polygon:
            msg = "Cannot decompose into rectangles. Something is not rectilinear!"
            if not ignore_non_rectilinear:
                logger.error(msg)
                assert False, msg
            else:
                logger.warning(msg)

        rectangles.append(box)
    return rectangles


def generate_lef_macro(cell_name: str,
                       size:lef.SIZE,
                       obs_geometries:List[Tuple[str,db.Shape]],
                       pin_geometries: Dict[str, List[Tuple[str, db.Shape]]],
                       pin_direction: Dict[str, lef.Direction],
                       pin_use: Dict[str, lef.Use],
                       site: str = "asap7sc7p5t",
                       scaling_factor: float = 1,
                       use_rectangles_only: bool = False,
                       ) -> lef.Macro:
    """
    Assemble a LEF MACRO structure containing the pin shapes.
    :param site: SITE name. Default is 'CORE'.
    :param cell_name: Name of the cell as it will appear in the LEF file.
    :param pin_geometries: A dictionary mapping pin names to geometries: Dict[pin name, List[(layer name, klayout Shape)]]
    :param pin_direction:
    :param pin_use:
    :param use_rectangles_only: Decompose all polygons into rectangles. Non-rectilinear shapes are dropped.
    :return: Returns a `lef.Macro` object containing the pin information of the cell.

    # TODO: FOREIGN statement (reference to GDS)
    """

    logger.debug("Generate LEF MACRO structure for {}.".format(cell_name))
    logger.debug(f"Scaling factor = {scaling_factor}.")

    f = scaling_factor

    pins = []
    # Create LEF Pin objects containing geometry information of the pins.
    for pin_name, ports in pin_geometries.items():

        layers = []

        for layer_name, shape in ports:
            # Convert all non-regions into a region
            region = db.Region()
            region.insert(shape)
            region.merge()
            if use_rectangles_only:
                # Decompose into rectangles.
                boxes = _decompose_region(region)
                region = db.Region()
                region.insert(boxes)

            geometries = []
            for p in region.each():
                polygon = p.to_simple_polygon()

                box = polygon.bbox()
                is_box = db.SimplePolygon(box) == polygon

                if is_box:
                    rect = lef.Rect((box.p1.x * f, box.p1.y * f), (box.p2.x * f, box.p2.y * f))
                    geometries.append(rect)
                else:
                    # Port is a polygon
                    # Convert `db.Point`s into LEF points.
                    points = [(p.x * f, p.y * f) for p in polygon.each_point()]
                    poly = lef.Polygon(points)
                    geometries.append(poly)

            layers.append((lef.Layer(layer_name), geometries))

        port = lef.Port(geometries=layers)


        # if pin_name not in pin_direction:
        #     msg = "I/O direction of pin '{}' is not defined.".format(pin_name)
        #     logger.error(msg)
        #     assert False, msg
        #
        # if pin_name not in pin_use:
        #     msg = "Use of pin '{}' is not defined. Must be one of (CLK, SIGNAL, POWER, ...)".format(pin_name)
        #     logger.error(msg)
        #     assert False, msg
        if pin_name=="VDD"  :
            pin = lef.Pin2(pin_name=pin_name,
                        direction=lef.Direction.INOUT,  # TODO: find direction
                        use=lef.Use.POWER,  # TODO: correct use
                        shape=lef.Shape.ABUTMENT,
                        port=port,
                        property={},
                        )
        elif pin_name=="VSS":
            pin = lef.Pin2(pin_name=pin_name,
                        direction=lef.Direction.INOUT,  # TODO: find direction
                        use=lef.Use.GROUND,  # TODO: correct use
                        shape=lef.Shape.ABUTMENT,
                        port=port,
                        property={},
                        )
        elif pin_name=="Y":
            pin = lef.Pin(pin_name=pin_name,
                        direction=lef.Direction.OUTPUT,  # TODO: find direction
                        use=lef.Use.SIGNAL,  # TODO: correct use
                        port=port,
                        property={},
                        )
        else :
            pin = lef.Pin(pin_name=pin_name,
                        direction=lef.Direction.INOUT,  # TODO: find direction
                        use=lef.Use.SIGNAL,  # TODO: correct use
                        port=port,
                        property={},
                        )
        pins.append(pin)

    #生成obstruction
    obs_layers=[]
    for obs_layername,shape2 in obs_geometries:
        
        region2 = db.Region()
        region2.insert(shape2)
        region2.merge()
        if use_rectangles_only:
            # Decompose into rectangles.
            boxes_obs = _decompose_region(region2)
            region2 = db.Region()
            region2.insert(boxes_obs)

        geometries2 = []
        for r in region2.each():
            polygon2 = r.to_simple_polygon()

            box2 = polygon2.bbox()
            is_box2 = db.SimplePolygon(box2) == polygon2

            if is_box2:
                rect2 = lef.Rect((box2.p1.x * f, box2.p1.y * f), (box2.p2.x * f, box2.p2.y * f))
                geometries2.append(rect2)
            else:
                # Port is a polygon
                # Convert `db.Point`s into LEF points.
                points2 = [(r.x * f, r.y * f) for r in polygon.each_point()]
                poly2 = lef.Polygon(points2)
                geometries2.append(poly2)

        obs_layers.append((lef.Layer(obs_layername), geometries2))

    obs=[lef.Obstruction(geometries=obs_layers)]
    


    macro = lef.Macro(
        name=cell_name,
        macro_class=lef.MacroClass.CORE,
        foreign=lef.Foreign(cell_name, lef.Point(0, 0)),
        size=size,
        origin=lef.Point(0, 0),
        symmetry={lef.Symmetry.X, lef.Symmetry.Y},
        site=site,
        pins=pins,
        obstructions=obs
    )

    return macro

