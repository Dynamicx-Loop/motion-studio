"""Explicit adapters for already measured values; no numerical recomputation."""
from __future__ import annotations


def metric(identity: str, value: float | None, unit: str, aggregation: str,
           population: str, pointer: str | None, stage: str = 'post_filter',
           status: str = 'recorded', reason: str | None = None) -> dict:
    return {'id': identity, 'value': value, 'unit': unit, 'aggregation': aggregation,
            'population': population, 'source_pointer': pointer,
            'trajectory_stage': stage, 'status': status, 'reason': reason}


def motion_metrics(row: dict) -> list[dict]:
    """Extents are clamped below-floor distances, never collision or force estimates."""
    values = [
        metric('visual_floor_min_height', row['visual_min_height_m'], 'm',
               'minimum over selected visual mesh vertices and all frames',
               'group-1 visual mesh geometry; horizontal Z=0 plane', '/visual_min_height_m'),
        metric('visual_floor_worst_below_floor_extent', max(0, -row['visual_min_height_m']) * 1000,
               'mm', 'max(0, -minimum height) * 1000',
               'group-1 visual mesh geometry; horizontal Z=0 plane', '/visual_min_height_m',
               status='derived'),
        metric('visual_floor_frames_below_minus_1mm', row['visual_penetration_frames_below_minus_1mm'],
               'frame', 'count of frames with minimum height < -0.001 m',
               f"all {row['frames']} exported frames", '/visual_penetration_frames_below_minus_1mm'),
        metric('configured_joint_limit_violations', row['joint_limit_violation_count_1e6'],
               'joint_frame', 'count of margins < -1e-6 rad',
               'all hinges, all frames; MJCF limits intersect config overrides',
               '/joint_limit_violation_count_1e6'),
        metric('configured_joint_limit_min_margin', row['joint_limit_min_margin_rad'], 'rad',
               'minimum over hinges and frames', 'configured joint limits', '/joint_limit_min_margin_rad'),
    ]
    for key, unit, order in [('joint_velocity_abs_rad_s', 'rad/s', 1),
                              ('joint_acceleration_abs_rad_s2', 'rad/s^2', 2)]:
        for aggregation, value in row[key].items():
            values.append(metric(f'{key}.{aggregation}', value, unit, aggregation,
                                 f'absolute order-{order} finite differences times fps^{order}; '
                                 'all hinges including constant fingers, all valid frame differences',
                                 f'/{key}/{aggregation}'))
    cost = row.get('solver_reported_cost')
    for aggregation in ('mean', 'max'):
        values.append(metric(f'solver_objective.{aggregation}', cost[aggregation] if cost else None,
                             'weighted_objective', aggregation, 'solver log aggregate; residual mixture',
                             f'/solver_reported_cost/{aggregation}' if cost else None,
                             'pre_filter', 'recorded' if cost else 'not_measured',
                             None if cost else 'No solver cost was recorded'))
    for side, stance in row.get('inferred_stance', {}).items():
        speed = stance.get('horizontal_speed_m_s')
        values.append(metric(f'{side}_ankle_stance_speed.mean', speed['mean'] if speed else None,
                             'm/s', 'mean over consecutive inferred-stance frames',
                             stance['definition'], f'/inferred_stance/{side}/horizontal_speed_m_s/mean',
                             status='recorded' if speed else 'not_measured',
                             reason=None if speed else 'No eligible stance frame pairs'))
    for identity, unit, reason in [
        ('self_collision_depth', 'm', row.get('self_collision', 'Not evaluated')),
        ('collision_geometry_floor_clearance', 'm', 'Visual-mesh metrics do not measure collision geometry'),
        ('selected_slot_floor_clearance', 'm', 'Not independently recorded in results.json'),
        ('contact_force', 'N', 'No dynamics or force measurement'),
        ('pre_filter_visual_floor_clearance', 'm', 'Saved arrays are not a recorded metric; no recomputation'),
        ('controller_tracking_error', 'm', 'No downstream controller execution in this cohort')]:
        values.append(metric(identity, None, unit, 'not measured', reason, None,
                             'not_measured', 'not_measured', reason))
    return values


def hand_metrics(row: dict, variant: str) -> list[dict]:
    """Physical hand-mesh membership is distinct from anatomical-zone precision."""
    k = '0' if variant == 'raw' else '32'
    measured = row[k]
    values = [metric('symmetric_sample_mean_distance', measured['symmetric_sample_mean_distance_mm'],
                     'mm', 'mean of the two directed nearest-sample mean distances',
                     'all learned robot slots and fixed target reference samples',
                     f'/{k}/symmetric_sample_mean_distance_mm', 'static')]
    for side in ('left', 'right'):
        values.extend([
            metric(f'{side}_actual_hand_slots', measured[side]['actual_hand'], 'slot',
                   'count', f"{measured[side]['slots']} source hand-labeled slots; physical hand meshes",
                   f'/{k}/{side}/actual_hand', 'static'),
            metric(f'{side}_actual_hand_coverage20mm', measured[side]['actual_hand_coverage20mm'],
                   'fraction', 'fraction within <=0.020 m of a projected source hand slot',
                   f"{measured[side]['hand_reference_samples']} actual-hand reference samples",
                   f'/{k}/{side}/actual_hand_coverage20mm', 'static')])
    return values
