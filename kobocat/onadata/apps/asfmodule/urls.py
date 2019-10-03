from django.conf.urls import patterns, include, url
from django.contrib import admin
from onadata.apps.asfmodule import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^profile_view/(?P<victim_id>\d+)/$', views.profile_view,name='profile_view'),
    url(r'^get_forms_data/$', views.get_forms_data,name='get_forms_data'),
    url(r'^get_data_view/$', views.get_data_view,name='get_data_view'),
    url(r'^get_forms_list/$', views.get_forms_list,name='get_forms_list'),
    url(r'^get_forms_html/$', views.get_forms_html,name='get_forms_html'),
    url(r'^get_districts/$', views.get_districts,name='get_districts'),
    url(r'^get_upazilas/$', views.get_upazilas,name='get_upazilas'),
    url(r'^get_unions/$', views.get_unions,name='get_unions'),
    url(r'^get_wards/$', views.get_wards,name='get_wards'),
    url(r'^case_list/$', views.case_list,name='case_list'),
    url(r'^add_case_form/$', views.add_case_form,name='add_case_form'),
    url(r'^insert_case_form/$', views.insert_case_form,name='insert_case_form'),
    url(r'^get_case_list/$', views.get_case_list,name='get_case_list'),
    url(r'^case_detail/(?P<case_id>\d+)/$', views.case_detail,name='case_detail'),
    url(r'^update_case_status/(?P<case_id>\d+)/$', views.update_case_status,name='update_case_status'),
    url(r'^get_victim_list/$', views.get_victim_list,name='get_victim_list'),
    url(r'^add_victim/(?P<case_id>\d+)/$', views.add_victim, name='add_victim'),
    url(r'^insert_victim/(?P<case_id>\d+)/$', views.insert_victim, name='insert_victim'),
    url(r'^edit_victim/(?P<victim_tbl_id>\d+)/$', views.edit_victim, name='edit_victim'),
    url(r'^update_victim/(?P<victim_tbl_id>\d+)/$', views.update_victim, name='update_victim'),
    url(r'^victim_status/(?P<victim_tbl_id>\d+)/$', views.victim_status, name='victim_status'),
    url(r'^victim_status_from_web/(?P<victim_tbl_id>\d+)/$', views.victim_status_from_web, name='victim_status_from_web'),
    url(r'^refer_victim/(?P<victim_id>[\w\-]+)/(?P<victim_tbl_id>\d+)/$', views.refer_victim, name='refer_victim'),
    url(r'^victim_profile/(?P<victim_tbl_id>\d+)/$', views.victim_profile, name='victim_profile'),
    url(r'^generate_pdf/$', views.generate_pdf, name='generate_pdf'),
    url(r'^victim_list/$', views.victim_list,name='victim_list'),
    url(r'^get_victims_list/$', views.get_victims_list,name='get_victims_list'),

    url(r'^services_to_other_institutes_list/$', views.services_to_other_institutes_list,name='services_to_other_institutes_list'),
    url(r'^get_services_to_other_institutes_list/$', views.get_services_to_other_institutes_list,name='get_services_to_other_institutes_list'),
    url(r'^services_to_other_institutes_form/$', views.services_to_other_institutes_form,name='services_to_other_institutes_form'),

    url(r'^capacity_building_list/$', views.capacity_building_list,name='capacity_building_list'),
    url(r'^get_capacity_building_list/$', views.get_capacity_building_list,name='get_capacity_building_list'),
    url(r'^capacity_building_form/$', views.capacity_building_form,name='capacity_building_form'),

    url(r'^event_list/$', views.event_list,name='event_list'),
    url(r'^get_event_list/$', views.get_event_list,name='get_event_list'),
    url(r'^event_form/$', views.event_form,name='event_form'),

    url(r'^ipt_show_list/$', views.ipt_show_list,name='ipt_show_list'),
    url(r'^get_ipt_show_list/$', views.get_ipt_show_list,name='get_ipt_show_list'),
    url(r'^ipt_show_form/$', views.ipt_show_form,name='ipt_show_form'),
    url(r'^ipt_profile/(?P<event_id>\d+)/$', views.ipt_profile, name='ipt_profile'),
    url(r'^get_events_forms_data/$', views.get_events_forms_data, name='get_events_forms_data'),

    url(r'^tea_stall_meeting_list/$', views.tea_stall_meeting_list,name='tea_stall_meeting_list'),
    url(r'^get_tea_stall_meeting_list/$', views.get_tea_stall_meeting_list,name='get_tea_stall_meeting_list'),
    url(r'^tea_stall_meeting_form/$', views.tea_stall_meeting_form,name='tea_stall_meeting_form'),
    url(r'^tea_stall_meeting_profile/(?P<event_id>\d+)/$', views.tea_stall_meeting_profile, name='tea_stall_meeting_profile'),

    url(r'^video_show_list/$', views.video_show_list,name='video_show_list'),
    url(r'^get_video_show_list/$', views.get_video_show_list,name='get_video_show_list'),
    url(r'^video_show_form/$', views.video_show_form,name='video_show_form'),
    url(r'^video_show_profile/(?P<event_id>\d+)/$', views.video_show_profile, name='video_show_profile'),

    url(r'^school_quiz_list/$', views.school_quiz_list,name='school_quiz_list'),
    url(r'^get_school_quiz_list/$', views.get_school_quiz_list,name='get_school_quiz_list'),
    url(r'^school_quiz_form/$', views.school_quiz_form,name='school_quiz_form'),
    url(r'^school_quiz_profile/(?P<event_id>\d+)/$', views.school_quiz_profile, name='school_quiz_profile'),

    url(r'^paper_clipping_list/$', views.paper_clipping_list,name='paper_clipping_list'),
    url(r'^get_paper_clipping_list/$', views.get_paper_clipping_list,name='get_paper_clipping_list'),
    url(r'^paper_clipping_form/$', views.paper_clipping_form,name='paper_clipping_form'),

    url(r'^dashboard/$', views.dashboard,name='dashboard'),
    url(r'^get_dashboard_data/$', views.get_dashboard_data,name='get_dashboard_data'),

    url(r'^medical_patient_report/$', views.medical_patient_report,name='medical_patient_report'),
    url(r'^get_medical_patient_report/$', views.get_medical_patient_report,name='get_medical_patient_report'),

    url(r'^medical_certificate_report/$', views.medical_certificate_report,name='medical_certificate_report'),
    url(r'^get_medical_certificate_report/$', views.get_medical_certificate_report,name='get_medical_certificate_report'),

    url(r'^medical_injuries_report/$', views.medical_injuries_report,name='medical_injuries_report'),
    url(r'^get_medical_injuries_report/$', views.get_medical_injuries_report,name='get_medical_injuries_report'),

    url(r'^medical_operations_report/$', views.medical_operations_report,name='medical_operations_report'),
    url(r'^get_medical_operations_report/$', views.get_medical_operations_report,name='get_medical_operations_report'),

    url(r'^legal_report/$', views.legal_report,name='legal_report'),
    url(r'^get_legal_report/$', views.get_legal_report,name='get_legal_report'),

    url(r'^rehab_report/$', views.rehab_report,name='rehab_report'),
    url(r'^get_rehab_report/$', views.get_rehab_report,name='get_rehab_report'),

    url(r'^physiotherapy_patient_report/$', views.physiotherapy_patient_report,name='physiotherapy_patient_report'),
    url(r'^get_physiotherapy_patient_report/$', views.get_physiotherapy_patient_report,name='get_physiotherapy_patient_report'),

    url(r'^physiotherapy_govt_hospital_report/$', views.physiotherapy_govt_hospital_report,name='physiotherapy_govt_hospital_report'),
    url(r'^get_physiotherapy_govt_hospital_report/$', views.get_physiotherapy_govt_hospital_report,name='get_physiotherapy_govt_hospital_report'),

    url(r'^physiotherapy_eclinic_report/$', views.physiotherapy_eclinic_report,name='physiotherapy_eclinic_report'),
    url(r'^get_physiotherapy_eclinic_report/$', views.get_physiotherapy_eclinic_report,name='get_physiotherapy_eclinic_report'),

    url(r'^physiotherapy_outreach_report/$', views.physiotherapy_outreach_report,name='physiotherapy_outreach_report'),
    url(r'^get_physiotherapy_outreach_report/$', views.get_physiotherapy_outreach_report,name='get_physiotherapy_outreach_report'),

    url(r'^physiotherapy_community_clinic_report/$', views.physiotherapy_community_clinic_report,name='physiotherapy_community_clinic_report'),
    url(r'^get_physiotherapy_community_clinic_report/$', views.get_physiotherapy_community_clinic_report,name='get_physiotherapy_community_clinic_report'),

    url(r'^physiotherapy_pressure_garment_report/$', views.physiotherapy_pressure_garment_report,name='physiotherapy_pressure_garment_report'),
    url(r'^get_medical_pressure_garment_report/$', views.get_medical_pressure_garment_report,name='get_medical_pressure_garment_report'),


    url(r'^psychotherapy_govt_hospital_report/$', views.psychotherapy_govt_hospital_report,name='psychotherapy_govt_hospital_report'),
    url(r'^get_psychotherapy_govt_hospital_report/$', views.get_psychotherapy_govt_hospital_report,name='get_psychotherapy_govt_hospital_report'),

    url(r'^psychotherapy_eclinic_report/$', views.psychotherapy_eclinic_report,name='psychotherapy_eclinic_report'),
    url(r'^get_psychotherapy_eclinic_report/$', views.get_psychotherapy_eclinic_report,name='get_psychotherapy_eclinic_report'),

    url(r'^psychotherapy_outreach_report/$', views.psychotherapy_outreach_report,name='psychotherapy_outreach_report'),
    url(r'^get_psychotherapy_outreach_report/$', views.get_psychotherapy_outreach_report,name='get_psychotherapy_outreach_report'),

    url(r'^psychotherapy_community_clinic_report/$', views.psychotherapy_community_clinic_report,name='psychotherapy_community_clinic_report'),
    url(r'^get_psychotherapy_community_clinic_report/$', views.get_psychotherapy_community_clinic_report,name='get_psychotherapy_community_clinic_report'),

    url(r'^psychotherapy_patient_report/$', views.psychotherapy_patient_report,name='psychotherapy_patient_report'),
    url(r'^get_psychotherapy_patient_report/$', views.get_psychotherapy_patient_report,name='get_psychotherapy_patient_report'),

    url(r'^referral_list/$', views.referral_list,name='referral_list'),
    url(r'^get_referral_list/$', views.get_referral_list,name='get_referral_list'),

    url(r'^call_center_report/$', views.call_center_report,name='call_center_report'),
    url(r'^get_call_center_report/$', views.get_call_center_report,name='get_call_center_report'),
    url(r'^call_center_form/$', views.call_center_form,name='call_center_form'),

    url(r'^consultancy_matrix/$', views.consultancy_matrix,name='consultancy_matrix'),
    url(r'^get_consultancy_matrix/$', views.get_consultancy_matrix,name='get_consultancy_matrix'),
    url(r'^consultancy_matrix_form/$', views.consultancy_matrix_form,name='consultancy_matrix_form'),
    url(r'^get_consultation_matrix_profile/(?P<id>\d+)/$', views.get_consultation_matrix_profile,name='get_consultation_matrix_profile'),
    url(r'^get_deliverable/$', views.get_deliverable,name='get_deliverable'),
    url(r'^update_deliverable/$', views.update_deliverable,name='update_deliverable'),

    url(r'^get-form/(?P<id_string>[^/]+)/$', views.get_form,name='get_form'),
    url(r'^get_form_access/(?P<id_string>[^/]+)/$', views.get_form_access,name='get_form_access'),
    url(r'^get_export/$', views.get_export,name='get_export'),
    url(r'^export/$', views.export,name='export'),

    url(r'^rsc_list/$', views.rsc_list,name='rsc_list'),
    url(r'^get_rsc_list/$', views.get_rsc_list,name='get_rsc_list'),
    url(r'^catchment_tree/(?P<rsc_id>\d+)/$', views.catchment_tree_test, name='catchment_tree'),
    url(r'^catchment_data_insert/$', views.catchment_data_insert, name='catchment_data_insert'),
    url(r'^add_rsc_form/$', views.add_rsc_form, name='add_rsc_form'),
    url(r'^beneficiary_progress_report/(?P<id>\d+)/$', views.beneficiary_progress_report,name='beneficiary_progress_report'),
    url(r'^get_progress_report_data/$', views.get_progress_report_data,name='get_progress_report_data'),
    url(r'^get_reintegration_sustainibility_data/$', views.get_reintegration_sustainibility_data,name='get_reintegration_sustainibility_data'),

    url(r'^events_from_csv_list/$', views.events_from_csv_list,name='events_from_csv_list'),
    url(r'^get_events_from_csv_list/$', views.get_events_from_csv_list,name='get_events_from_csv_list'),
    url(r'^add_events_from_csv_form/$', views.add_events_from_csv_form,name='add_events_from_csv_form'),
    url(r'^edit_events_from_csv/(?P<events_tbl_id>\d+)/$', views.edit_events_from_csv,name='edit_events_from_csv'),
    url(r'^delete_events_from_csv/(?P<events_tbl_id>\d+)/$', views.delete_events_from_csv,name='delete_events_from_csv'),

    url(r'^case_study_list/$', views.case_study_list,name='case_study_list'),
    url(r'^get_case_study_list/$', views.get_case_study_list,name='get_case_study_list'),
    url(r'^case_study_form/$', views.case_study_form,name='case_study_form'),

    url(r'^msc_story_list/$', views.msc_story_list,name='msc_story_list'),
    url(r'^get_msc_story_list/$', views.get_msc_story_list,name='get_msc_story_list'),
    url(r'^msc_story_form/$', views.msc_story_form,name='msc_story_form'),

    )
