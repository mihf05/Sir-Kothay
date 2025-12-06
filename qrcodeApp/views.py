import qrcode
from PIL import Image
from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.staticfiles import finders
from io import BytesIO
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .models import QRCode
from django.urls import reverse

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
import os

from dashboard.models import UserDetails

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch


@login_required(login_url='login')
def generate_qr_code_with_logo(request):
    slug = get_object_or_404(UserDetails, user=request.user).slug
    
    # Check if the user already has a QR code
    if QRCode.objects.filter(user=request.user).exists():
        messages.info(request, "You already have your one-time QR code.")
        return redirect(reverse('home'))
    
    # Build the URL using the URL name
    url_to_encode = request.build_absolute_uri(reverse('show_broadcast_messages', kwargs={'user_slug': slug}))

    # Generate the QR code
    qr = qrcode.QRCode(
        version=1,  # controls the size of the QR Code
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction for logo insertion
        box_size=10,
        border=4,
    )
    qr.add_data(url_to_encode)
    qr.make(fit=True)

    # Create an image from the QR code
    img = qr.make_image(fill='black', back_color='white').convert("RGBA")  # Convert to RGBA for transparency support

    # Open the logo image
    logo_path = finders.find('images/logo.png')
    if logo_path:
        logo = Image.open(logo_path).convert("RGBA")  # Ensure the logo has an alpha channel

        # Calculate the size of the logo and resize it
        qr_width, qr_height = img.size
        logo = logo.resize((90, 60), Image.LANCZOS)

        # Create a transparent layer the same size as the QR code
        overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
        logo_position = ((qr_width - 90) // 2, (qr_height - 60) // 2)

        # Paste the logo onto the overlay
        overlay.paste(logo, logo_position, logo)

        # Merge QR code and logo overlay
        img = Image.alpha_composite(img, overlay)

    # Save the image to a BytesIO buffer
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)

    # Create a SimpleUploadedFile to save the image
    qr_image = SimpleUploadedFile(
        name=f"qr_code_with_logo_slug_{slug}.png",
        content=img_buffer.read(),
        content_type='image/png'
    )

    # Create or update the QRCode object in the database
    qr_code, created = QRCode.objects.get_or_create(user=request.user)
    qr_code.image.save(qr_image.name, qr_image)
    qr_code.save()
    
    messages.success(request, "QR Code with logo generated successfully!")

    return redirect(reverse('home'))

@login_required(login_url='login')
def download_qr_code(request):
    # Get the QR code for the logged-in user or return 404 if not found
    qr_code = get_object_or_404(QRCode, user=request.user)

    # Get the file path
    qr_code_path = qr_code.image.path

    # Ensure the file exists before serving
    if not os.path.exists(qr_code_path):
        raise Http404("QR code file not found.")

    # Open file and set headers to force download
    response = FileResponse(open(qr_code_path, 'rb'))
    response['Content-Type'] = 'application/octet-stream'  # Ensures it's always downloaded
    response['Content-Disposition'] = 'attachment; filename="qr_code.png"'

    return response

@login_required(login_url='login')
def download_qr_with_info(request):
    # Get user details
    user_details = get_object_or_404(UserDetails, user=request.user)
    qr_code = get_object_or_404(QRCode, user=request.user)

    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title = Paragraph("Scan the QR Code", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))

    # Load images
    profile_img_path = user_details.profile_image.path if user_details.profile_image and os.path.exists(user_details.profile_image.path) else None
    qr_img_path = qr_code.image.path

    # Left side: profile image and info
    left_flowables = []
    if profile_img_path:
        left_flowables.append(RLImage(profile_img_path, width=2*inch, height=2*inch))
        left_flowables.append(Spacer(1, 12))
    info_text = f"<b>Name:</b> {request.user.get_full_name() or request.user.username}<br/>" \
                f"<b>Email:</b> {request.user.email}<br/>" \
                f"<b>Phone:</b> {user_details.phone_number}<br/>" \
                f"<b>Organization:</b> {user_details.organization}<br/>" \
                f"<b>Designation:</b> {user_details.designation}"
    left_flowables.append(Paragraph(info_text, styles['Normal']))

    # Right side: QR code
    right_flowables = []
    right_flowables.append(RLImage(qr_img_path, width=3.25*inch, height=3.25*inch))
    right_flowables.append(Spacer(1, 12))
    # Create table
    data = [
        [left_flowables, right_flowables]
    ]

    table = Table(data, colWidths=[3*inch, 3*inch])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    story.append(table)

    doc.build(story)
    buffer.seek(0)

    response = FileResponse(buffer, as_attachment=True, filename='info_with_qr.pdf')
    return response
