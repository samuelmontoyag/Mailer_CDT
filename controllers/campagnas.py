# -*- coding: utf-8 -*-
from flask import (
    Blueprint,
    current_app,
    Response,
    abort,
    jsonify,
    request,
    session,
    redirect,
    flash,
    render_template,
    url_for
)
from flask_login import login_required, current_user
from sqlalchemy import Table
import mailchimp
from utils import get_mailchimp_api
from eventos import get_event_data
from time import timezone
from datetime import datetime, timedelta
import json
import math

campagnas = Blueprint('campagnas', __name__)


def initialize_app(app):
    app.register_blueprint(campagnas)


@campagnas.route("/campagnas", methods=['GET', 'POST'])
@login_required
def index(message=None, folder=None):
    data = {
        'message': message,
        'current_folder': folder
    }
    return render_template('campagnas/list.html', **data)


def paginate_data(data, pagina, folder=0, per_page=25):
    data['page'] = pagina
    data['next_num'] = pagina + 1
    data['prev_num'] = pagina - 1
    data['pages'] = math.ceil(data['total'] / per_page)
    data['per_page'] = per_page
    if pagina > 0:
        data['has_previus'] = True
    if pagina < data['pages']:
        data['has_next'] = True
    return data


@campagnas.route("/campagnas/ajax/listar", methods=['GET', 'POST'])
@campagnas.route("/campagnas/ajax/listar/<int:pagina>", methods=['GET', 'POST'])
@login_required
def ajax_listar_campagnas(pagina=0):
    per_page = 25
    m = get_mailchimp_api()
    campaignList = m.campaigns.list(start=pagina)
    campaignList = paginate_data(campaignList, pagina)
    return json.dumps(campaignList)


@campagnas.route("/campagnas/ajax/buscar", methods=['POST'])
@login_required
def ajax_buscar_campagnas(pagina=0):
    per_page = 25
    filters = {'title': request.form.get('title', ''),
               'exact': False,
               'status': ','.join(request.form.getlist('status')),
               'folder_id': ','.join(request.form.getlist('folder_id')),
               'sendtime_start': request.form.get('sendtime_start', ''),
               'sendtime_end': request.form.get('sendtime_end', ''),
               'folder_id': request.form.get('folder_id', '')
               }
    m = get_mailchimp_api()
    campaignList = m.campaigns.list(filters=filters)
    campaignList = paginate_data(campaignList, pagina, per_page=per_page)

    return json.dumps(campaignList)


@campagnas.route("/campagnas/ajax/folders", methods=['GET', 'POST'])
def ajax_folder_list():
    return json.dumps(get_mailchimp_api().folders.list("campaign"))


@campagnas.route("/campagnas/folder/<folder>", methods=['GET', 'POST'])
@login_required
def folder(folder=None):
    return index(None, folder)


@campagnas.route("/campagnas/folder/setArea", methods=['POST'])
@login_required
def changeFolder():
    folder_id = request.form['area']
    id_camp = request.form['id']
    try:
        m = get_mailchimp_api()
        details = m.campaigns.update(id_camp, 'options',
                                     {'folder_id': folder_id})
    except mailchimp.Error, e:
        return "Ha ocurrido un error con mailchimp", e

    return index(None, details['data']['folder_id'])


@campagnas.route("/campagnas/folder/remove/<area_id>", methods=['POST'])
@login_required
def deleteFolder(area_id):
    area = area_id
    folderType = "campaign"
    try:
        print(area)
        m = get_mailchimp_api()
        folder_id = m.folders.delete(area, folderType)
        print(folder_id)
    except mailchimp.Error, e:
        return "Ha ocurrido un error con mailchimp", e
    return index(None, folder_id)


@campagnas.route("/campagnas/folder/add/", methods=['POST'])
@login_required
def addFolder():
    name = request.form['name']
    folderType = "campaign"
    try:
        m = get_mailchimp_api()
        folder_id = m.folders.add(name, folderType)
    except mailchimp.Error, e:
        return "Ha ocurrido un error al intentar conectar con mailchimp"
    return index(None, folder_id)


@campagnas.route("/campagnas/create", methods=['GET'])
@login_required
def create():
    try:
        m = get_mailchimp_api()
        lists = m.lists.list(sort_field='web', limit=100)
        template_lists = m.templates.list()
        folderList = m.folders.list("campaign")
    except mailchimp.Error, e:
        return "Ha ocurrido un error con mailchimp<br>"+str(e)
    data = {
        'lists': lists['data'],
        'template_lists': template_lists['user'],
        'areaList': folderList
    }
    return render_template('campagnas/create.html',
                           title="Crear campañas",
                           **data)


@campagnas.route("/campagnas/create", methods=['POST'])
@login_required
def create2():
    type = 'regular'
    options = {
        'list_id': request.form['emailList'],
        'subject': request.form['subject'],
        'from_email': request.form['outgoinEmail'],
        'from_name': request.form['outgoinName'],
        'title': request.form['campaignName'],
        'auto_footer': False,
        'folder_id': request.form['folder']
    }
    content = {
        'html': request.form['html']
    }
    # se quita como ya no existen eventos
    # event_id = int(request.form['event_id'])
    # if (event_id > 0):
    #     event_data = get_event_data(event_id)
    #     content = {
    #         'html': replace_tags(request.form['html'], event_data)
    #     }
    m = get_mailchimp_api()
    try:
        if 'id' in request.form:
            cid = request.form['id']
            detailsVar = m.campaigns.update(cid, 'options', options)
            details2 = m.campaigns.update(cid, 'content', content)
            errors = detailsVar['errors']
            detailsVar = detailsVar['data']
        else:
            detailsVar = m.campaigns.create(type, options, content)
    except mailchimp.Error, e:
        return index("<div class='alert alert-danger'>Ha ocurrido un error \
                      con mailchimp "+str(e)+"</div>")
    return details(detailsVar["id"])


@campagnas.route("/campagnas/detalles/<id>", methods=['GET'])
@login_required
def details(id):
    try:
        m = get_mailchimp_api()
        details = m.campaigns.list({'campaign_id': id})
        list_id = details['data'][0].get("list_id", 0)
        current_list = m.lists.list(filters={'list_id': list_id})

    except mailchimp.Error, e:
        flash("Ha ocurrido un error: " + str(e), "error")
    campaign = details['data'][0]
    set_current_gmt(campaign)
    if campaign['status'] == "sent":
        campaign['status'] = "Enviado"
    elif campaign['status'] == "save":
        campaign['status'] = "Guardado"
    elif campaign['status'] == "sending":
        campaign['status'] = "Enviando"
    data = {
        'campaign': campaign,
        'current_list': current_list['data'][0]
    }
    return render_template('campagnas/details.html',
                           title="Detalles",
                           **data)


@campagnas.route("/campagnas/edit/<id_>", methods=['GET'])
@login_required
def edit(id_):
    try:
        m = get_mailchimp_api()
        details = m.campaigns.list({'campaign_id': id_})
        content = m.campaigns.content(id_)
        lists = m.lists.list(limit=100)
        template_lists = m.templates.list()
        folderList = m.folders.list("campaign")
    except mailchimp.Error, e:
        return index("Ha ocurrido un error con mailchimp"+str(e))

    html = (clean_html(content['html']))

    data = {
        'campaign': details['data'][0],
        'html': html,
        'lists': lists['data'],
        'template_lists': template_lists['user'],
        'areaList': folderList
    }
    return render_template('campagnas/edit.html',
                           title="Editar campaña",
                           **data)


@campagnas.route("/campagnas/clone/<id>", methods=['GET'])
@login_required
def clone(id):
    try:
        m = get_mailchimp_api()
        details = m.campaigns.list({'campaign_id': id})
        content = m.campaigns.content(id)
        lists = m.lists.list(limit=100)
        template_lists = m.templates.list()
        folderList = m.folders.list("campaign")
    except mailchimp.Error, e:
        return index("Ha ocurrido un error con mailchimp"+str(e))
    html = replace_rewards_unsubcribe(content['html'])
    details['data'][0]['id'] = None
    data = {
        'campaign': details['data'][0],
        'html': html,
        'lists': lists['data'],
        'template_lists': template_lists['user'],
        'areaList': folderList
    }
    return render_template('campagnas/edit.html',
                           title="Editar campaña",
                           **data)


@campagnas.route("/campagnas/send", methods=['POST'])
@login_required
def send():
    id_ = request.form['id']
    try:
        m = get_mailchimp_api()
        status = m.campaigns.send(id_)
    except mailchimp.Error, e:
        flash("Se encontraron errores con mailchimp " + str(e), "error")
    return redirect(url_for(".details", id=id_))


@campagnas.route("/campagnas/sendTest", methods=['POST'])
@login_required
def sendTest():
    emails = request.form.getlist('email')
    campaignId = request.form['campaignId']
    try:
        m = get_mailchimp_api()
        details = m.campaigns.send_test(campaignId, emails)
        flash("pruebas enviadas correctamente", "success")
    except mailchimp.Error, e:
        flash("Ha ocurrido un error al conectar con mailchimp:\n" + str(e),
              "error")
        return redirect(url_for(".details", id=campaignId))
    return redirect(url_for(".details", id=campaignId))


@campagnas.route("/campagnas/delete/<campaign_id>", methods=['POST'])
@login_required
def delete(campaign_id):
    try:
        m = get_mailchimp_api()
        status = m.campaigns.delete(campaign_id)
    except mailchimp.CampaignDoesNotExistError:
        return json.dumps({"error": u"la campaña no existe"})
    except mailchimp.Error, e:
        return json.dumps({"error": u"Ha ocurrido un error con mailchimp"})
    return json.dumps({"ok": u"campaña eliminada"})


def replace_tags(html, data):
    html = html.replace("*|EVENT_NAME|*", data['event_name'])
    html = html.replace("*|EVENT_DATE|*", str(data['event_start_date']))
    html = html.replace("http://*|EVENT_URL|*", data['url'])
    html = html.replace("*|EVENT_URL|*", data['url'])

    if html.find('*|REWARDS|*') < 0:
        html += '<div style="display:none">*|REWARDS|*</div>'
    return html


def replace_rewards_unsubcribe(html):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html)
    url_rewards = 'http://www.mailchimp.com/monkey-rewards'
    url_unsubcribe = '.com/unsubscribe'
    url_archive = 'campaign-archive'
    for link in soup.findAll('a'):
        if url_unsubcribe in link.get('href'):
            link['href'] = '*|UNSUB|*'
        elif (url_archive in link.get('href', '')):
            link['href'] = '*|ARCHIVE|*'
        elif (url_rewards in link.get('href')):
            link.find_parent().decompose()
    return unicode(soup)


def set_current_gmt(campaign):
    format = "%Y-%m-%d %H:%M:%S"
    keys = ['create_time', 'send_time']
    for key in keys:
        if campaign[key]:
            new_date = datetime.strptime(campaign[key], format)
            campaign[key] = new_date - timedelta(seconds=timezone)
    return campaign


def clean_html(html):
    from bs4 import BeautifulSoup
    html = replace_rewards_unsubcribe(html)
    soup = BeautifulSoup(html)
    mailchimp_datas = soup.findAll('table', {'id': 'canspamBarWrapper'})
    for data in mailchimp_datas:
        data.findParent().decompose()
    return unicode(soup)
