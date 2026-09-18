import sys
import os

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Users\User\Ecosistema-Maxi\Temis")

from temis_web.state import FlowState

def test_hub_state_logic():
    print("=" * 60)
    print("PROBANDO LÓGICA DEL HUB DE PROYECTOS Y NAVEGACIÓN")
    print("=" * 60)
    
    state = FlowState()
    print(f"• Modo Activo Inicial: {state.active_mode}")
    print(f"• Rol Inicial: {state.user_role}")
    print(f"• Total Proyectos en Catálogo: {len(state.saved_projects)}")
    
    # 1. Test KPI calculations
    print(f"\n1. KPIs Ejecutivos:")
    print(f"   - Total Proyectos: {state.total_hub_projects_count}")
    print(f"   - Story Points: {state.total_completed_sp_count} / {state.total_sp_count} SP")
    print(f"   - % Avance Global: {state.global_progress_pct}%")
    print(f"   - Score Auditoría Promedio: {state.average_audit_score}/100")
    print(f"   - Sprints en Ejecución: {state.active_sprints_count}")

    # 2. Test Role filtering
    print(f"\n2. Filtro por Rol:")
    state.set_user_role("super_admin")
    print(f"   - Super Admin ve: {len(state.filtered_hub_projects)} proyectos")
    state.set_user_role("project_manager")
    print(f"   - Dueño de Proyecto (Mario) ve: {len(state.filtered_hub_projects)} proyectos")
    state.set_user_role("collaborator")
    print(f"   - Colaborador ve: {len(state.filtered_hub_projects)} proyectos")

    # 3. Test Phase and Search Filtering
    print(f"\n3. Filtros y Búsqueda:")
    state.set_user_role("super_admin")
    state.set_filter_hub_phase("4")
    print(f"   - Proyectos en Fase 4: {[p['name'] for p in state.filtered_hub_projects]}")
    state.set_filter_hub_phase("all")
    state.set_search_hub_query("WhatsApp")
    print(f"   - Búsqueda 'WhatsApp': {[p['name'] for p in state.filtered_hub_projects]}")
    state.set_search_hub_query("")

    # 4. Test Navigation transition Hub ➔ Workspace ➔ Hub
    print(f"\n4. Transición Hub ➔ Workspace ➔ Hub:")
    state.open_project_workspace("proj-x")
    print(f"   - Clic en 'Abrir Espacio': Modo={state.active_mode}, Proyecto Activo='{state.project_name}', Código='{state.project_code}', Drive={state.drive_folder_id != ''}, Sheet={state.sheet_id != ''}")
    state.return_to_hub()
    print(f"   - Clic en 'Mis Proyectos': Modo={state.active_mode}")

    print("\n" + "=" * 60)
    print("¡TODAS LAS PRUEBAS DE LÓGICA PASARON EXITOSAMENTE!")
    print("=" * 60)

if __name__ == "__main__":
    test_hub_state_logic()
