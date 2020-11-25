from django.template import loader
from django.core.mail import send_mail


def send_email_to_team_members(team,mail_body,mail_subject):
    context = {'body':mail_body}
    html_content = loader.render_to_string('userauth/info_mail.html', context)
    send_mail(
        mail_subject,
        mail_body,'info.the.flow.app@gmail.com',
        team.members.values_list('user__email',flat=True),
        html_message = html_content, fail_silently = False
    )

def send_email_to_object_watchers(object,mail_body,mail_subject):
    # sending email notification
    context = {'body':mail_body}
    html_content = loader.render_to_string('userauth/info_mail.html', context)
    send_mail(
        mail_subject,
        mail_body,'info.the.flow.app@gmail.com',
        object.watched_by.values_list('user__email',flat=True),
        html_message = html_content,fail_silently = False
    )
    #-------

def send_email_to(email,mail_body,mail_subject):
    context = {'body':mail_body}
    html_content = loader.render_to_string('userauth/info_mail.html', context)
    send_mail(mail_subject, mail_body,'info.the.flow.app@gmail.com',[email], html_message = html_content, fail_silently = False)
