import services
import sims4.commands
import sims4.resources


@sims4.commands.Command('spawn_tenants', command_type=sims4.commands.CommandType.Live)
def spawn_tenants(_connection=None):
    output = sims4.commands.CheatOutput(_connection)
    try:
        output("Starting...")
        template_manager = services.get_instance_manager(sims4.resources.Types.SIM_TEMPLATE)
        tenant_template_ids = [0x0000000000057632, 0x000000000005764A, 0x0000000000055B44, 0x0000000000055B45, 0x0000000000055B47, 0x00000000000573A7, 0x00000000000573A8, 0x00000000000573A9, 0x00000000000573B4, 0x00000000000573B5, 0x00000000000573B6, 0x00000000000573B7, 0x00000000000573B8, 0x00000000000573B9, 0x00000000000573BA, 0x00000000000573BB]
        tenant_household_names = ["Lu", "Kham", "Shadows", "Reevera", "McFierce", "Song", "Roomies", "Brock", "Pawn", "Newlyweds", "Sage", "Lee", "Cragg", "Boulder", "Yarmellino", "Robertson"]

        templates = [template_manager.get(template_id) for template_id in tenant_template_ids]

        for idx in range(len(templates)):
            household = templates[idx].create_household(0, None, family_name=tenant_household_names[idx])
            household.move_into_zone(0)
            output(f"Spawned {household.name}")
        output("Done")
    except (Exception,) as e:
        output(str(e))



